"""Phase 5 tests — Demand Forecast and Planner Review endpoints and migration."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import engine
from app.models.forecast_review import ForecastReview
from scripts.migrate_forecast_reviews import run_migration
from tests.test_auth import _get_token


def test_01_forecast_endpoints_without_token_return_401(client: TestClient) -> None:
    assert client.get("/api/forecast/skus").status_code == 401
    assert client.get("/api/forecast/SKU001").status_code == 401
    assert client.post("/api/forecast/SKU001/review", json={}).status_code == 401


def test_02_forecast_sku_list_returns_30_skus(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/skus", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    skus = resp.json()
    assert len(skus) == 30
    assert skus[0]["sku_id"] == "SKU001"
    assert "wape" in skus[0]
    assert "bias" in skus[0]


def test_03_sku_detail_returns_365_actual_observations(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["actual_sales"]) == 365


def test_04_sku_detail_returns_30_forecast_observations(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["forecast_results"]) == 30


def test_05_actual_dates_ordered_ascending(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    dates = [o["sales_date"] for o in resp.json()["actual_sales"]]
    assert dates == sorted(dates)


def test_06_forecast_dates_ordered_ascending(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    dates = [o["forecast_date"] for o in resp.json()["forecast_results"]]
    assert dates == sorted(dates)


def test_07_actual_history_ends_on_or_before_demo_analysis_date(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert data["actual_end_date"] <= "2026-08-05"


def test_08_forecast_begins_after_demo_analysis_date(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert data["forecast_start_date"] > "2026-08-05"
    assert data["forecast_start_date"] == "2026-08-06"


def test_09_wape_matches_forecast_metrics(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert data["wape"] == 0.1247


def test_10_bias_matches_forecast_metrics(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU001", headers={"Authorization": f"Bearer {token}"})
    data = resp.json()
    assert data["bias"] == -0.0431


def test_11_unknown_sku_returns_404(client: TestClient) -> None:
    token = _get_token(client, "warehouse.staff")
    resp = client.get("/api/forecast/SKU9999", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_12_planner_can_submit_review(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    try:
        resp = client.post(
            "/api/forecast/SKU001/review",
            headers={"Authorization": f"Bearer {planner_token}"},
            json={
                "review_status": "ACCEPTED_AS_BASELINE",
                "planner_comment": "Baseline forecast verified by planner.",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["reviewer_username"] == "planner"
        assert data["review_status"] == "ACCEPTED_AS_BASELINE"
        assert data["planner_comment"] == "Baseline forecast verified by planner."
    finally:
        # Cleanup test review
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM forecast_reviews WHERE reviewer_username = 'planner'"))
            conn.commit()


def test_13_warehouse_staff_receives_403_when_submitting(client: TestClient) -> None:
    staff_token = _get_token(client, "warehouse.staff")
    resp = client.post(
        "/api/forecast/SKU001/review",
        headers={"Authorization": f"Bearer {staff_token}"},
        json={
            "review_status": "ACCEPTED_AS_BASELINE",
            "planner_comment": "Staff review attempt.",
        },
    )
    assert resp.status_code == 403


def test_14_warehouse_manager_receives_403_when_submitting(client: TestClient) -> None:
    manager_token = _get_token(client, "warehouse.manager")
    resp = client.post(
        "/api/forecast/SKU001/review",
        headers={"Authorization": f"Bearer {manager_token}"},
        json={
            "review_status": "ACCEPTED_AS_BASELINE",
            "planner_comment": "Manager review attempt.",
        },
    )
    assert resp.status_code == 403


def test_15_blank_comment_is_rejected(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    resp = client.post(
        "/api/forecast/SKU001/review",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={
            "review_status": "ACCEPTED_AS_BASELINE",
            "planner_comment": "   ",
        },
    )
    assert resp.status_code in (400, 422)


def test_16_invalid_review_status_is_rejected(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    resp = client.post(
        "/api/forecast/SKU001/review",
        headers={"Authorization": f"Bearer {planner_token}"},
        json={
            "review_status": "INVALID_STATUS",
            "planner_comment": "Valid comment text.",
        },
    )
    assert resp.status_code in (400, 422)


def test_17_saved_review_persists(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    try:
        # Submit
        resp = client.post(
            "/api/forecast/SKU002/review",
            headers={"Authorization": f"Bearer {planner_token}"},
            json={
                "review_status": "MONITOR",
                "planner_comment": "Monitoring high bias.",
            },
        )
        assert resp.status_code == 201

        # Fetch detail and verify persisted review
        get_resp = client.get(
            "/api/forecast/SKU002",
            headers={"Authorization": f"Bearer {planner_token}"},
        )
        assert get_resp.status_code == 200
        detail = get_resp.json()
        assert detail["latest_review"] is not None
        assert detail["latest_review"]["review_status"] == "MONITOR"
        assert detail["latest_review"]["planner_comment"] == "Monitoring high bias."
    finally:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM forecast_reviews WHERE reviewer_username = 'planner'"))
            conn.commit()


def test_18_new_review_does_not_modify_forecast_results(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    with engine.connect() as conn:
        before_count = conn.execute(text("SELECT COUNT(*) FROM forecast_results")).fetchone()[0]

    try:
        client.post(
            "/api/forecast/SKU001/review",
            headers={"Authorization": f"Bearer {planner_token}"},
            json={
                "review_status": "MONITOR",
                "planner_comment": "Test non-modification.",
            },
        )
        with engine.connect() as conn:
            after_count = conn.execute(text("SELECT COUNT(*) FROM forecast_results")).fetchone()[0]
        assert before_count == after_count
    finally:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM forecast_reviews WHERE reviewer_username = 'planner'"))
            conn.commit()


def test_19_new_review_does_not_modify_forecast_metrics(client: TestClient) -> None:
    planner_token = _get_token(client, "planner")
    with engine.connect() as conn:
        before_metric = conn.execute(
            text("SELECT wape, bias FROM forecast_metrics WHERE sku_id = 'SKU001'")
        ).fetchone()

    try:
        client.post(
            "/api/forecast/SKU001/review",
            headers={"Authorization": f"Bearer {planner_token}"},
            json={
                "review_status": "MONITOR",
                "planner_comment": "Test non-modification of metrics.",
            },
        )
        with engine.connect() as conn:
            after_metric = conn.execute(
                text("SELECT wape, bias FROM forecast_metrics WHERE sku_id = 'SKU001'")
            ).fetchone()
        assert before_metric == after_metric
    finally:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM forecast_reviews WHERE reviewer_username = 'planner'"))
            conn.commit()


def test_20_migration_is_idempotent() -> None:
    assert run_migration() is True
    assert run_migration() is True


def test_21_forecast_reviews_foreign_key_is_valid() -> None:
    with engine.connect() as conn:
        fk_errors = conn.execute(text("PRAGMA foreign_key_check(forecast_reviews)")).fetchall()
        assert len(fk_errors) == 0
