"""Shared pytest fixtures for the backend test suite."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    A single TestClient instance shared across the whole test session.
    Uses the same application (and therefore the same database) as the
    dev server — the existing SQLite file at data/generated/vims_ai_demo.db.
    No separate test database is created; the DB is read-only in Phase 1.
    """
    with TestClient(app) as c:
        yield c
