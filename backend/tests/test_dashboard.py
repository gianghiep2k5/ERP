"""Phase 3 tests — GET /api/dashboard/summary."""
from fastapi.testclient import TestClient
from tests.test_auth import _get_token


def test_dashboard_summary_unauthorized(client: TestClient) -> None:
    """Dashboard endpoint requires JWT authentication."""
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 401


def test_dashboard_summary_authorized_staff(client: TestClient) -> None:
    """Warehouse Staff can view dashboard summary."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_skus"] == 30
    assert data["total_lots"] == 120
    assert data["total_on_hand_qty"] > 0
    assert data["pending_recommendations"] > 0
    assert data["stockout_count"] == 32
    assert data["expiry_count"] == 28
    assert data["transfer_count"] == 28
    assert data["normal_count"] == 32
    assert data["analysis_date"] == "2026-08-05"
    assert data["latest_update"] is not None


def test_dashboard_summary_authorized_manager(client: TestClient) -> None:
    """Warehouse Manager can view dashboard summary."""
    token = _get_token(client, "warehouse.manager")
    resp = client.get(
        "/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
