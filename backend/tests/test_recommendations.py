"""Phase 6 tests — Recommendation Approval and Audit Log endpoints."""
import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from tests.test_auth import _get_token

# Seed database absolute path (relative to repo root)
MAIN_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "generated", "vims_ai_demo.db")
)


@pytest.fixture(scope="function")
def isolated_client():
    """
    Creates a temporary copy of vims_ai_demo.db for mutation tests
    so main database is never modified by test runs.
    """
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_vims_ai_demo.db")
    shutil.copyfile(MAIN_DB_PATH, temp_db_path)

    test_engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
    )

    from sqlalchemy import event

    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(test_engine, "connect", set_sqlite_pragma)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()
    test_engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Read & Auth Tests
# ---------------------------------------------------------------------------

def test_01_recommendation_endpoints_without_token_return_401(client: TestClient) -> None:
    assert client.get("/api/recommendations").status_code == 401
    assert client.get("/api/recommendations/REC0001").status_code == 401
    assert client.get("/api/audit").status_code == 401
    assert client.patch("/api/recommendations/REC0001/quantity", json={}).status_code == 401
    assert client.post("/api/recommendations/REC0001/approve", json={}).status_code == 401
    assert client.post("/api/recommendations/REC0001/reject", json={}).status_code == 401


def test_02_recommendation_list_returns_40_rows(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/recommendations", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 40
    assert len(data["items"]) == 40


def test_03_all_three_recommendation_types_present(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/recommendations", headers={"Authorization": f"Bearer {token}"})
    types = {item["recommendation_type"] for item in resp.json()["items"]}
    assert "REPLENISHMENT" in types
    assert "TRANSFER" in types
    assert "EXPIRY_ACTION" in types


def test_04_effective_qty_coalesce_logic(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/recommendations", headers={"Authorization": f"Bearer {token}"})
    items = resp.json()["items"]
    for item in items:
        expected_effective = item["adjusted_qty"] if item["adjusted_qty"] is not None else item["proposed_qty"]
        assert item["effective_qty"] == expected_effective


def test_06_recommendation_detail_joins(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/recommendations/REC0001", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["recommendation_id"] == "REC0001"
    assert data["sku_name"] is not None
    assert data["status"] == "APPROVED"
    assert len(data["audit_history"]) >= 1


def test_07_audit_list_returns_seeded_rows(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 24
    assert len(data["items"]) == 24


def test_08_to_11_read_role_access(client: TestClient) -> None:
    roles = ["warehouse.staff", "planner", "branch.manager", "quality.manager"]
    for role in roles:
        token = _get_token(client, role)
        r_rec = client.get("/api/recommendations", headers={"Authorization": f"Bearer {token}"})
        assert r_rec.status_code == 200, f"Role {role} failed reading recommendations"
        r_aud = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
        assert r_aud.status_code == 200, f"Role {role} failed reading audit"


def test_12_to_15_non_approver_roles_forbidden(client: TestClient) -> None:
    forbidden_roles = ["warehouse.staff", "planner", "branch.manager", "quality.manager"]
    for role in forbidden_roles:
        token = _get_token(client, role)
        r_mod = client.patch(
            "/api/recommendations/REC0002/quantity",
            headers={"Authorization": f"Bearer {token}"},
            json={"adjusted_qty": 3000, "comment": "Unauthorized edit"},
        )
        assert r_mod.status_code == 403, f"Role {role} should be 403 on modify"

        r_app = client.post(
            "/api/recommendations/REC0002/approve",
            headers={"Authorization": f"Bearer {token}"},
            json={"comment": "Unauthorized approve"},
        )
        assert r_app.status_code == 403, f"Role {role} should be 403 on approve"


# ---------------------------------------------------------------------------
# Mutation & Workflow Tests (Using Isolated DB Fixture)
# ---------------------------------------------------------------------------

def test_16_to_19_quantity_modification(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # REC0002 is PENDING with proposed_qty 3314
    resp = isolated_client.patch(
        "/api/recommendations/REC0002/quantity",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"adjusted_qty": 3000, "comment": "Adjusting for shelf capacity."},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "PENDING"
    assert data["proposed_qty"] == 3314  # proposed_qty immutable
    assert data["adjusted_qty"] == 3000
    assert data["effective_qty"] == 3000

    # Audit history includes MODIFIED entry
    history = data["audit_history"]
    latest_audit = history[-1]
    assert latest_audit["action"] == "MODIFIED"
    assert latest_audit["before_status"] == "PENDING"
    assert latest_audit["after_status"] == "PENDING"
    assert latest_audit["actor_username"] == "warehouse.manager"


def test_20_21_approval_workflow(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # REC0002 is PENDING
    resp = isolated_client.post(
        "/api/recommendations/REC0002/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Approved after review."},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "APPROVED"
    history = data["audit_history"]
    latest_audit = history[-1]
    assert latest_audit["action"] == "APPROVED"
    assert latest_audit["actor_username"] == "warehouse.manager"


def test_22_23_rejection_workflow(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # REC0004 is PENDING
    resp = isolated_client.post(
        "/api/recommendations/REC0004/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Rejected due to overstocking."},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "REJECTED"
    history = data["audit_history"]
    latest_audit = history[-1]
    assert latest_audit["action"] == "REJECTED"


def test_24_to_26_mandatory_comments(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # Blank comment on modify
    r1 = isolated_client.patch(
        "/api/recommendations/REC0002/quantity",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"adjusted_qty": 3000, "comment": "   "},
    )
    assert r1.status_code in (400, 422)

    # Blank comment on approve
    r2 = isolated_client.post(
        "/api/recommendations/REC0002/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": ""},
    )
    assert r2.status_code in (400, 422)

    # Blank comment on reject
    r3 = isolated_client.post(
        "/api/recommendations/REC0002/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "   "},
    )
    assert r3.status_code in (400, 422)


def test_27_adjusted_qty_non_positive_rejected(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")
    resp = isolated_client.patch(
        "/api/recommendations/REC0002/quantity",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"adjusted_qty": 0, "comment": "Zero qty test"},
    )
    assert resp.status_code in (400, 422)


def test_28_unknown_recommendation_404(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")
    resp = isolated_client.post(
        "/api/recommendations/REC9999/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Approved"},
    )
    assert resp.status_code == 404


def test_29_to_31_double_processing_conflict_409(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # REC0001 is already APPROVED in seed data
    r_app = isolated_client.post(
        "/api/recommendations/REC0001/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Double approve"},
    )
    assert r_app.status_code == 409

    r_rej = isolated_client.post(
        "/api/recommendations/REC0001/reject",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Reject approved rec"},
    )
    assert r_rej.status_code == 409

    r_mod = isolated_client.patch(
        "/api/recommendations/REC0001/quantity",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"adjusted_qty": 1000, "comment": "Modify approved rec"},
    )
    assert r_mod.status_code == 409


def test_33_audit_id_sequence_generation(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    resp = isolated_client.post(
        "/api/recommendations/REC0002/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Testing audit ID sequence."},
    )
    assert resp.status_code == 200
    data = resp.json()
    latest_audit = data["audit_history"][-1]
    # Max numeric suffix in seed audit_logs is 38 -> next is AUD0039
    assert latest_audit["audit_id"] == "AUD0039"


def test_36_37_inventory_and_forecast_tables_unchanged(isolated_client: TestClient) -> None:
    manager_token = _get_token(isolated_client, "warehouse.manager")

    # Approve recommendation REC0002
    isolated_client.post(
        "/api/recommendations/REC0002/approve",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={"comment": "Checking non-modification of inventory/forecast tables."},
    )

    # Verify inventory_balances count is still 120
    inv_resp = isolated_client.get("/api/inventory", headers={"Authorization": f"Bearer {manager_token}"})
    assert inv_resp.json()["total"] == 120

    # Verify forecast SKUs count is still 30
    fc_resp = isolated_client.get("/api/forecast/skus", headers={"Authorization": f"Bearer {manager_token}"})
    assert len(fc_resp.json()) == 30
