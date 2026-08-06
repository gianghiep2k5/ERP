"""Phase 7 Integrated Scenario Acceptance Tests.

Validates:
1. Scenario 1: Expiry Risk to Recommendation Approval (Dynamic Selection)
2. Scenario 2: Demand Forecast & Planner Review RBAC
3. Scenario 3: Transfer Recommendation Decision Support
4. Complete RBAC Matrix across all 5 user roles
5. Protected Table Fingerprint Integrity before & after scenarios
"""
import hashlib
import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from tests.test_auth import _get_token

# Main DB path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MAIN_DB_PATH = os.path.join(REPO_ROOT, "data", "generated", "vims_ai_demo.db")


def _compute_table_fingerprint(db_path: str, table_name: str) -> str:
    """Computes a SHA-256 fingerprint hash for all rows in a table."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    rows = conn.execute(f"SELECT * FROM {table_name} ORDER BY ROWID").fetchall()
    conn.close()
    content = str(rows).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


@pytest.fixture(scope="function")
def isolated_scenario_client():
    """
    Creates an isolated copy of vims_ai_demo.db in a temporary directory
    to ensure main database is never modified by scenario runs.
    """
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "scenario_vims_ai_demo.db")
    shutil.copyfile(MAIN_DB_PATH, temp_db_path)

    engine = create_engine(
        f"sqlite:///{temp_db_path}",
        connect_args={"check_same_thread": False},
    )

    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(engine, "connect", set_sqlite_pragma)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client, temp_db_path

    app.dependency_overrides.clear()
    engine.dispose()
    shutil.rmtree(temp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Scenario 1: Expiry Risk to Recommendation Approval (Dynamic Selection)
# ---------------------------------------------------------------------------

def test_scenario_1_expiry_risk_to_approval(isolated_scenario_client):
    client, db_path = isolated_scenario_client

    # 0. Fingerprint protected tables before scenario
    fp_inv_before = _compute_table_fingerprint(db_path, "inventory_balances")
    fp_lots_before = _compute_table_fingerprint(db_path, "lots")

    # 1. Authenticate as Warehouse Manager
    token = _get_token(client, "warehouse.manager")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Dynamic candidate selection procedure:
    #    Retrieve expiry risk list, filter by Critical, fall back to High
    risk_resp = client.get("/api/expiry-risk", headers=headers)
    assert risk_resp.status_code == 200
    all_risk_lots = risk_resp.json()["items"]

    critical_lots = [item for item in all_risk_lots if item["risk_band"] == "Critical"]
    high_lots = [item for item in all_risk_lots if item["risk_band"] == "High"]
    candidate_risk_lots = critical_lots + high_lots

    assert len(candidate_risk_lots) > 0, "No Critical or High risk lots found in expiry risk centre!"

    # 3. Inspect each lot's related recommendations to find first eligible PENDING pair
    selected_lot = None
    selected_rec = None

    for lot in candidate_risk_lots:
        l_id = lot["lot_id"]
        rec_resp = client.get(f"/api/recommendations?lot_id={l_id}&status=PENDING", headers=headers)
        if rec_resp.status_code == 200:
            recs = rec_resp.json()["items"]
            if recs:
                selected_lot = lot
                selected_rec = recs[0]
                break

    assert selected_lot is not None and selected_rec is not None, "No eligible (Critical/High Risk Lot, PENDING Rec) pair found!"

    # 4. Explicit regression assertions on selected pair
    lot_id = selected_lot["lot_id"]
    rec_id = selected_rec["recommendation_id"]
    orig_proposed_qty = selected_rec["proposed_qty"]

    # Retrieve detailed lot & recommendation data
    lot_detail_resp = client.get(f"/api/expiry-risk/{lot_id}", headers=headers)
    assert lot_detail_resp.status_code == 200
    lot_detail = lot_detail_resp.json()

    rec_detail_resp = client.get(f"/api/recommendations/{rec_id}", headers=headers)
    assert rec_detail_resp.status_code == 200
    rec_detail = rec_detail_resp.json()

    # Assert lot IDs match explicitly
    assert rec_detail["lot_id"] == lot_detail["lot_id"], f"Selected recommendation {rec_id} lot_id ({rec_detail['lot_id']}) does not match expiry risk lot_id ({lot_detail['lot_id']})!"
    assert rec_detail["status"] == "PENDING"

    # 5. Modify quantity with mandatory comment
    target_adjusted_qty = orig_proposed_qty + 100 if orig_proposed_qty < 1000 else orig_proposed_qty - 100
    mod_resp = client.patch(
        f"/api/recommendations/{rec_id}/quantity",
        headers=headers,
        json={"adjusted_qty": target_adjusted_qty, "comment": f"Scenario 1: Adjusted quantity for lot {lot_id}."},
    )
    assert mod_resp.status_code == 200
    mod_data = mod_resp.json()

    assert mod_data["proposed_qty"] == orig_proposed_qty  # proposed_qty unchanged
    assert mod_data["adjusted_qty"] == target_adjusted_qty
    assert mod_data["effective_qty"] == target_adjusted_qty
    assert mod_data["status"] == "PENDING"
    assert mod_data["audit_history"][-1]["action"] == "MODIFIED"

    # 6. Approve recommendation with mandatory comment
    app_resp = client.post(
        f"/api/recommendations/{rec_id}/approve",
        headers=headers,
        json={"comment": f"Scenario 1: Approved effective quantity {target_adjusted_qty} for lot {lot_id}."},
    )
    assert app_resp.status_code == 200
    app_data = app_resp.json()

    assert app_data["status"] == "APPROVED"
    assert app_data["audit_history"][-1]["action"] == "APPROVED"
    assert app_data["audit_history"][-1]["actor_username"] == "warehouse.manager"

    # 7. Verify protected tables fingerprints after scenario
    fp_inv_after = _compute_table_fingerprint(db_path, "inventory_balances")
    fp_lots_after = _compute_table_fingerprint(db_path, "lots")
    assert fp_inv_before == fp_inv_after, "inventory_balances was modified by Scenario 1!"
    assert fp_lots_before == fp_lots_after, "lots was modified by Scenario 1!"


# ---------------------------------------------------------------------------
# Scenario 2: Demand Forecast & Planner Review RBAC
# ---------------------------------------------------------------------------

def test_scenario_2_forecast_planner_review(isolated_scenario_client):
    client, db_path = isolated_scenario_client

    # 0. Fingerprint protected tables before scenario
    fp_fc_results_before = _compute_table_fingerprint(db_path, "forecast_results")
    fp_fc_metrics_before = _compute_table_fingerprint(db_path, "forecast_metrics")

    # 1. Authenticate as Planner
    planner_token = _get_token(client, "planner")
    planner_headers = {"Authorization": f"Bearer {planner_token}"}

    # 2. Retrieve SKU001 forecast detail
    detail_resp = client.get("/api/forecast/SKU001", headers=planner_headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["actual_sales"]) == 365
    assert detail["actual_sales"][-1]["sales_date"] == "2026-08-05"
    assert len(detail["forecast_results"]) == 30
    assert detail["forecast_results"][0]["forecast_date"] == "2026-08-06"
    assert detail["wape"] == 0.1247
    assert detail["bias"] == -0.0431

    # 3. Submit Planner Review
    rev_resp = client.post(
        "/api/forecast/SKU001/review",
        headers=planner_headers,
        json={
            "review_status": "ACCEPTED_AS_BASELINE",
            "planner_comment": "Scenario 2: Validated against promotional sales calendar.",
        },
    )
    assert rev_resp.status_code in (200, 201)
    rev_data = rev_resp.json()
    assert rev_data["reviewer_username"] == "planner"
    assert rev_data["review_status"] == "ACCEPTED_AS_BASELINE"

    # 4. Verify review persists in detail
    recheck_resp = client.get("/api/forecast/SKU001", headers=planner_headers)
    assert recheck_resp.json()["latest_review"]["planner_comment"] == "Scenario 2: Validated against promotional sales calendar."

    # 5. Verify forecast_results and forecast_metrics remain 100% unchanged
    fp_fc_results_after = _compute_table_fingerprint(db_path, "forecast_results")
    fp_fc_metrics_after = _compute_table_fingerprint(db_path, "forecast_metrics")
    assert fp_fc_results_before == fp_fc_results_after
    assert fp_fc_metrics_before == fp_fc_metrics_after

    # 6. Authenticate as Warehouse Manager and verify review is visible read-only, but posting review fails with 403
    manager_token = _get_token(client, "warehouse.manager")
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    m_detail = client.get("/api/forecast/SKU001", headers=manager_headers).json()
    assert m_detail["latest_review"]["planner_comment"] == "Scenario 2: Validated against promotional sales calendar."

    m_post = client.post(
        "/api/forecast/SKU001/review",
        headers=manager_headers,
        json={"review_status": "MONITOR", "planner_comment": "Unauthorized manager review"},
    )
    assert m_post.status_code == 403, "Warehouse Manager should receive 403 on forecast review"


# ---------------------------------------------------------------------------
# Scenario 3: Transfer Recommendation Decision Support
# ---------------------------------------------------------------------------

def test_scenario_3_transfer_recommendation(isolated_scenario_client):
    client, db_path = isolated_scenario_client

    fp_inv_before = _compute_table_fingerprint(db_path, "inventory_balances")

    manager_token = _get_token(client, "warehouse.manager")
    headers = {"Authorization": f"Bearer {manager_token}"}

    # Find a PENDING TRANSFER recommendation
    list_resp = client.get("/api/recommendations?recommendation_type=TRANSFER&status=PENDING", headers=headers)
    assert list_resp.status_code == 200
    pending_transfers = list_resp.json()["items"]
    assert len(pending_transfers) > 0

    target_rec = pending_transfers[0]
    rec_id = target_rec["recommendation_id"]

    # Approve Transfer recommendation
    app_resp = client.post(
        f"/api/recommendations/{rec_id}/approve",
        headers=headers,
        json={"comment": "Scenario 3: Approved stock transfer proposal for operational balancing."},
    )
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "APPROVED"

    # Verify inventory_balances remains unchanged (decision support only!)
    fp_inv_after = _compute_table_fingerprint(db_path, "inventory_balances")
    assert fp_inv_before == fp_inv_after, "inventory_balances modified by transfer approval!"


# ---------------------------------------------------------------------------
# Full RBAC & Protected Fingerprint Verification
# ---------------------------------------------------------------------------

def test_full_rbac_and_database_fingerprint_integrity(isolated_scenario_client):
    client, db_path = isolated_scenario_client

    # Tables that must never be mutated during any scenario
    protected_tables = [
        "public_products",
        "skus",
        "locations",
        "users",
        "lots",
        "inventory_balances",
        "sales_history",
        "forecast_metrics",
        "forecast_results",
    ]

    before_fps = {t: _compute_table_fingerprint(db_path, t) for t in protected_tables}

    # Verify role permissions matrix
    roles_test = {
        "warehouse.manager": {"can_review_fc": False, "can_mutate_rec": True},
        "planner": {"can_review_fc": True, "can_mutate_rec": False},
        "warehouse.staff": {"can_review_fc": False, "can_mutate_rec": False},
        "branch.manager": {"can_review_fc": False, "can_mutate_rec": False},
        "quality.manager": {"can_review_fc": False, "can_mutate_rec": False},
    }

    for role, perms in roles_test.items():
        token = _get_token(client, role)
        h = {"Authorization": f"Bearer {token}"}

        # Check forecast review permission
        fc_res = client.post("/api/forecast/SKU001/review", headers=h, json={"review_status": "MONITOR", "planner_comment": "RBAC check"})
        if perms["can_review_fc"]:
            assert fc_res.status_code in (200, 201), f"Role {role} should be allowed to review forecast"
        else:
            assert fc_res.status_code == 403, f"Role {role} should be forbidden (403) to review forecast"

        # Check recommendation mutation permission
        rec_res = client.post("/api/recommendations/REC0004/approve", headers=h, json={"comment": "RBAC check"})
        if perms["can_mutate_rec"]:
            assert rec_res.status_code in (200, 409), f"Role {role} should be allowed to mutate rec"
        else:
            assert rec_res.status_code == 403, f"Role {role} should be forbidden (403) to mutate rec"

    # Verify protected table fingerprints after all tests
    after_fps = {t: _compute_table_fingerprint(db_path, t) for t in protected_tables}
    for t in protected_tables:
        assert before_fps[t] == after_fps[t], f"Protected table {t} was mutated during scenario testing!"
