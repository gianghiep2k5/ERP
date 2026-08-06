"""Phase 2 tests — Login, JWT, /api/auth/me, protected routes, role guard.

Scope (per implementation plan Phase 2):
  - login success and failure
  - JWT decoding via /api/auth/me
  - protected route returns 401 without a token
  - reusable require_role guard returns 403 for unauthorised role

Recommendation approve/reject/modify endpoints are NOT tested here;
those belong exclusively to Phase 6.
"""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _login(client: TestClient, username: str, password: str) -> dict:
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def _get_token(client: TestClient, username: str = "warehouse.manager") -> str:
    resp = _login(client, username, "Demo@123")
    assert resp.status_code == 200, f"Could not obtain token for {username}"
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_success(client: TestClient) -> None:
    """Valid credentials return HTTP 200 with an access_token and correct role."""
    resp = _login(client, "warehouse.manager", "Demo@123")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "warehouse.manager"
    assert data["role"] == "Warehouse Manager"


def test_login_wrong_password(client: TestClient) -> None:
    """Wrong password returns HTTP 401."""
    resp = _login(client, "warehouse.manager", "WrongPassword!")
    assert resp.status_code == 401


def test_login_unknown_user(client: TestClient) -> None:
    """Unknown username returns HTTP 401 (not 404 — avoids username enumeration)."""
    resp = _login(client, "nonexistent.user", "Demo@123")
    assert resp.status_code == 401


def test_login_response_does_not_contain_password_hash(client: TestClient) -> None:
    """Login response must never expose password_hash."""
    resp = _login(client, "warehouse.staff", "Demo@123")
    assert resp.status_code == 200
    payload = resp.json()
    assert "password_hash" not in payload


# ---------------------------------------------------------------------------
# /api/auth/me  — JWT decoding
# ---------------------------------------------------------------------------

def test_me_returns_user_fields(client: TestClient) -> None:
    """/me returns user_id, username, and role — no password_hash."""
    token = _get_token(client, "planner")
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "planner"
    assert data["role"] == "Planner"
    assert "user_id" in data
    assert "password_hash" not in data


def test_me_without_token_returns_401(client: TestClient) -> None:
    """/me without Authorization header returns HTTP 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    """/me with a tampered token returns HTTP 401."""
    resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Role guard — require_role returns 403 for unauthorised role
# ---------------------------------------------------------------------------

def test_role_guard_warehouse_staff_is_read_only(client: TestClient) -> None:
    """
    The reusable require_role(APPROVER_ROLES) guard must return HTTP 403
    when the current user is Warehouse Staff.

    We exercise this via a lightweight test endpoint registered only in this
    test module — no recommendation endpoints are called (those are Phase 6).
    """
    from fastapi import Depends
    from typing import Annotated
    from app.dependencies import require_role, APPROVER_ROLES
    from app.models.user import User
    from app.main import app

    # Register a temporary test route on the live app.
    test_route = "/api/test/approver-guard"

    @app.get(test_route, include_in_schema=False)
    def _guarded(
        _user: Annotated[User, Depends(require_role(APPROVER_ROLES))],
    ) -> dict:
        return {"ok": True}

    # Warehouse Staff token → 403
    staff_token = _get_token(client, "warehouse.staff")
    resp = client.get(
        test_route,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert resp.status_code == 403, (
        f"Expected 403 for Warehouse Staff, got {resp.status_code}"
    )

    # Warehouse Manager token → 200
    manager_token = _get_token(client, "warehouse.manager")
    resp = client.get(
        test_route,
        headers={"Authorization": f"Bearer {manager_token}"},
    )
    assert resp.status_code == 200
