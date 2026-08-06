"""Phase 3 tests — GET /api/inventory and GET /api/inventory/{inventory_id}."""
from fastapi.testclient import TestClient
from tests.test_auth import _get_token


def test_inventory_list_unauthorized(client: TestClient) -> None:
    """Inventory list requires authentication."""
    resp = client.get("/api/inventory")
    assert resp.status_code == 401


def test_inventory_list_total_count(client: TestClient) -> None:
    """Inventory list contains 120 total records before pagination."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/inventory",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 120
    assert len(data["items"]) == 120


def test_inventory_fefo_sorting(client: TestClient) -> None:
    """Default inventory listing places earlier expiry dates first (FEFO)."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/inventory",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    expiry_dates = [item["expiry_date"] for item in items]
    assert expiry_dates == sorted(expiry_dates)


def test_inventory_filtering(client: TestClient) -> None:
    """Filters by scenario and category work correctly."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/inventory?scenario=stockout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 32
    assert all(item["scenario"] == "stockout" for item in items)

    resp_cat = client.get(
        "/api/inventory?category=Fresh%20Milk",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_cat.status_code == 200
    cat_items = resp_cat.json()["items"]
    assert all(item["category"] == "Fresh Milk" for item in cat_items)


def test_inventory_detail_success(client: TestClient) -> None:
    """GET /api/inventory/INV0001 returns full joined inventory balance detail."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/inventory/INV0001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inventory_id"] == "INV0001"
    assert data["lot_id"] == "LOT0001"
    assert data["sku_id"] == "SKU001"
    assert data["location_id"] == "LOC01"
    assert data["on_hand_qty"] == 550
    assert "days_to_expiry" in data
    assert "fefo_priority" in data


def test_inventory_detail_not_found(client: TestClient) -> None:
    """GET /api/inventory/INV9999 returns 404."""
    token = _get_token(client, "warehouse.staff")
    resp = client.get(
        "/api/inventory/INV9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
