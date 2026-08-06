"""Phase 3 tests — GET /api/lots and GET /api/lots/{lot_id}."""
from fastapi.testclient import TestClient
from tests.test_auth import _get_token


def test_lots_list_unauthorized(client: TestClient) -> None:
    """Lots list requires authentication."""
    resp = client.get("/api/lots")
    assert resp.status_code == 401


def test_lots_list_success(client: TestClient) -> None:
    """GET /api/lots returns 120 total records."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/lots",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 120
    assert len(data["items"]) == 120


def test_lot_detail_joins(client: TestClient) -> None:
    """
    GET /api/lots/{lot_id} correctly joins SKU, Public Product, Location,
    Inventory Balance, and linked recommendations.
    """
    token = _get_token(client, "warehouse.staff")
    # LOT0005 has a recommendation (REC0001) in recommendations.csv
    resp = client.get(
        "/api/lots/LOT0005",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Lot & FEFO fields
    assert data["lot_id"] == "LOT0005"
    assert "days_to_expiry" in data
    assert "fefo_position" in data
    assert data["fefo_total"] == 4  # Each SKU has 4 lots

    # SKU fields
    assert data["sku_id"] == "SKU002"
    assert data["sku_name"] is not None

    # Public Product fields
    assert data["public_product_id"] == "PUB001"
    assert data["product_name"] is not None
    assert data["source_url"].startswith("https://www.vinamilk.com.vn")

    # Inventory Balance fields
    assert data["inventory_id"] == "INV0005"
    assert data["location_id"] == "LOC01"
    assert data["on_hand_qty"] == 234

    # Recommendations linked
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1
    rec = data["recommendations"][0]
    assert rec["recommendation_id"] == "REC0001"
    assert rec["proposed_qty"] == 3256
    assert rec["adjusted_qty"] == 2604
    assert rec["effective_qty"] == 2604  # COALESCE(2604, 3256)


def test_lot_detail_not_found(client: TestClient) -> None:
    """GET /api/lots/LOT9999 returns 404."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/lots/LOT9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
