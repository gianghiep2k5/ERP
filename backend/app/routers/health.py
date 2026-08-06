"""GET /api/health — database ping and per-table row counts."""
import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.database import get_table_counts

router = APIRouter(prefix="/api", tags=["health"])

# Record server start time so the health endpoint can report uptime.
_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    db_row_counts: dict[str, int]
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse, summary="Database ping and row counts")
def health() -> Any:
    """
    Returns:
    - **status**: "ok" if the database is reachable.
    - **db_row_counts**: row count for each of the 11 application tables.
    - **uptime_seconds**: seconds since the server process started.
    """
    counts = get_table_counts()
    return HealthResponse(
        status="ok",
        db_row_counts=counts,
        uptime_seconds=round(time.time() - _START_TIME, 1),
    )
