"""Phase 4 tests — Explainable Expiry Risk Centre services and endpoints."""
from fastapi.testclient import TestClient
from tests.test_auth import _get_token
from app.services.expiry_risk import (
    compute_lot_expiry_risk,
    determine_risk_band,
    get_proposed_actions,
)


def test_01_endpoint_without_token_returns_401(client: TestClient) -> None:
    resp = client.get("/api/expiry-risk")
    assert resp.status_code == 401


def test_02_warehouse_staff_can_read(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_03_warehouse_manager_can_read(client: TestClient) -> None:
    token = _get_token(client, "warehouse.manager")
    resp = client.get("/api/expiry-risk", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_04_list_returns_all_120_lots(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 120
    assert len(data["items"]) == 120


def test_05_low_risk_case(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT0001", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    item = resp.json()
    assert item["risk_band"] == "Low"
    assert item["days_to_expiry"] == 180
    assert item["projected_surplus"] == 0.0


def test_06_medium_risk_case(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT0010", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    item = resp.json()
    assert item["risk_band"] == "Medium"
    assert item["days_to_expiry"] == 34


def test_07_high_risk_case(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT0025", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    item = resp.json()
    assert item["risk_band"] == "High"
    assert item["days_to_expiry"] == 19
    assert item["projected_surplus"] > 0


def test_08_critical_risk_case(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT0009", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    item = resp.json()
    assert item["risk_band"] == "Critical"
    assert item["days_to_expiry"] == 15
    assert item["surplus_ratio"] >= 0.50


def test_09_expired_edge_case_fixture() -> None:
    """Controlled unit test for expired lot edge case (days_to_expiry <= 0)."""
    assessment = compute_lot_expiry_risk(
        lot_id="LOT_EXPIRED_TEST",
        sku_id="SKU001",
        sku_name="Test Milk",
        category="Fresh Milk",
        expiry_date_str="2026-08-01",  # 4 days past 2026-08-05
        manufacturing_date_str="2026-02-01",
        available_qty=100,
        on_hand_qty=100,
        inventory_id="INV_TEST",
        location_id="LOC01",
        location_name="Warehouse",
        recent_30d_sales_qty=300,
        sku_forecasts=[],
    )
    assert assessment.days_to_expiry == -4
    assert assessment.risk_band == "Expired"
    assert assessment.risk_score == 100.0
    assert assessment.forecast_consumption_before_expiry == 0.0
    assert assessment.projected_surplus == 100.0
    assert "Quarantine the lot immediately" in assessment.proposed_actions


def test_10_projected_surplus_calculation() -> None:
    """Test projected surplus = MAX(available - forecast, 0)."""
    # Available = 500, forecast = 200 => surplus = 300
    res1 = compute_lot_expiry_risk(
        lot_id="L1", sku_id="S1", sku_name="N", category="C",
        expiry_date_str="2026-08-20", manufacturing_date_str="2026-02-01",
        available_qty=500, on_hand_qty=500, inventory_id="I1", location_id="LOC01",
        location_name="W", recent_30d_sales_qty=300,
        sku_forecasts=[("2026-08-10", 100), ("2026-08-15", 100)],
    )
    assert res1.forecast_consumption_before_expiry == 200.0
    assert res1.projected_surplus == 300.0
    assert res1.projected_shortage == 0.0


def test_11_projected_shortage_calculation() -> None:
    """Test projected shortage = MAX(forecast - available, 0)."""
    # Available = 100, forecast = 300 => shortage = 200, surplus = 0
    res2 = compute_lot_expiry_risk(
        lot_id="L2", sku_id="S2", sku_name="N", category="C",
        expiry_date_str="2026-08-20", manufacturing_date_str="2026-02-01",
        available_qty=100, on_hand_qty=100, inventory_id="I2", location_id="LOC01",
        location_name="W", recent_30d_sales_qty=300,
        sku_forecasts=[("2026-08-10", 150), ("2026-08-15", 150)],
    )
    assert res2.forecast_consumption_before_expiry == 300.0
    assert res2.projected_surplus == 0.0
    assert res2.projected_shortage == 200.0


def test_12_surplus_ratio_with_available_qty_zero() -> None:
    """Test surplus_ratio = projected_surplus / MAX(available_qty, 1) when available_qty=0."""
    res = compute_lot_expiry_risk(
        lot_id="L0", sku_id="S0", sku_name="N", category="C",
        expiry_date_str="2026-08-20", manufacturing_date_str="2026-02-01",
        available_qty=0, on_hand_qty=0, inventory_id="I0", location_id="LOC01",
        location_name="W", recent_30d_sales_qty=300,
        sku_forecasts=[("2026-08-10", 50)],
    )
    assert res.available_qty == 0
    assert res.surplus_ratio == 0.0


def test_13_forecast_rows_used_when_available() -> None:
    """Forecast consumption uses forecast_results when 1 <= days_to_expiry <= 30."""
    res = compute_lot_expiry_risk(
        lot_id="LF", sku_id="SF", sku_name="N", category="C",
        expiry_date_str="2026-08-15", manufacturing_date_str="2026-02-01",
        available_qty=200, on_hand_qty=200, inventory_id="IF", location_id="LOC01",
        location_name="W", recent_30d_sales_qty=300,
        sku_forecasts=[("2026-08-07", 30), ("2026-08-10", 40), ("2026-08-20", 100)],
    )
    # Forecasts up to 2026-08-15: 30 + 40 = 70
    assert res.forecast_consumption_before_expiry == 70.0
    assert res.forecast_method == "30-day forecast"


def test_14_recent_demand_fallback_when_forecasts_unavailable() -> None:
    """Fallback to (recent_avg_demand * days_to_expiry) when forecast rows are empty."""
    res = compute_lot_expiry_risk(
        lot_id="LFB", sku_id="SFB", sku_name="N", category="C",
        expiry_date_str="2026-08-15", manufacturing_date_str="2026-02-01",
        available_qty=200, on_hand_qty=200, inventory_id="IFB", location_id="LOC01",
        location_name="W", recent_30d_sales_qty=300,  # avg daily = 10.0
        sku_forecasts=[],
    )
    # 10 days left * 10.0 = 100.0
    assert res.forecast_consumption_before_expiry == 100.0
    assert res.forecast_method == "Recent daily demand fallback"


def test_15_reason_generation_contains_calculated_values(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT0009", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    item = resp.json()
    assert "Critical" in item["explanation"]
    assert "58.3%" in item["explanation"] or "58.2%" in item["explanation"] or "1435" in item["explanation"]
    assert "15 days" in item["explanation"]


def test_16_action_generation_matches_risk_band() -> None:
    assert get_proposed_actions("Expired") == [
        "Quarantine the lot immediately",
        "Escalate to Quality Manager",
        "Block normal FEFO dispatch pending quality decision",
    ]
    assert get_proposed_actions("Critical") == [
        "Prioritise immediate FEFO dispatch",
        "Review transfer opportunity",
        "Escalate to Quality Manager",
        "Monitor daily",
    ]


def test_17_risk_band_filter(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk?risk_band=Critical", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 4
    assert all(i["risk_band"] == "Critical" for i in items)


def test_18_sku_and_category_filters(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk?sku_id=SKU003", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 4
    assert all(i["sku_id"] == "SKU003" for i in items)


def test_19_unknown_lot_returns_404(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/expiry-risk/LOT9999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_20_no_hard_coded_lot_result() -> None:
    """Verify determine_risk_band uses mathematical inputs, not hardcoded strings."""
    assert determine_risk_band(10, 50, 0.60) == "Critical"
    assert determine_risk_band(25, 30, 0.35) == "High"
    assert determine_risk_band(50, 10, 0.15) == "Medium"
    assert determine_risk_band(100, 0, 0.0) == "Low"
    assert determine_risk_band(0, 10, 0.50) == "Expired"
