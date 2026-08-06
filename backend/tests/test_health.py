"""Phase 1 tests — GET /api/health."""
from fastapi.testclient import TestClient

EXPECTED_TABLES = [
    "public_products",
    "skus",
    "locations",
    "users",
    "lots",
    "inventory_balances",
    "sales_history",
    "forecast_metrics",
    "forecast_results",
    "recommendations",
    "audit_logs",
]

EXPECTED_COUNTS = {
    "public_products": 15,
    "skus": 30,
    "locations": 3,
    "users": 5,
    "lots": 120,
    "inventory_balances": 120,
    "sales_history": 10950,
    "forecast_metrics": 30,
    "forecast_results": 900,
    "recommendations": 40,
    "audit_logs": 24,
}


def test_health_status_ok(client: TestClient) -> None:
    """Health endpoint must return HTTP 200 and status 'ok'."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_all_tables_present(client: TestClient) -> None:
    """Health response must contain row counts for all 11 application tables."""
    response = client.get("/api/health")
    assert response.status_code == 200
    counts = response.json()["db_row_counts"]
    for table in EXPECTED_TABLES:
        assert table in counts, f"Missing table in health response: {table}"


def test_health_row_counts_match_seed(client: TestClient) -> None:
    """Row counts must match the seeded dataset_summary.json values."""
    response = client.get("/api/health")
    assert response.status_code == 200
    counts = response.json()["db_row_counts"]
    for table, expected in EXPECTED_COUNTS.items():
        assert counts[table] == expected, (
            f"Row count mismatch for '{table}': "
            f"expected {expected}, got {counts[table]}"
        )


def test_health_uptime_is_positive(client: TestClient) -> None:
    """Uptime must be a non-negative number."""
    response = client.get("/api/health")
    assert response.status_code == 200
    uptime = response.json()["uptime_seconds"]
    assert isinstance(uptime, (int, float))
    assert uptime >= 0


def test_health_no_auth_required(client: TestClient) -> None:
    """Health endpoint must be accessible without an Authorization header."""
    response = client.get("/api/health", headers={})
    assert response.status_code == 200
