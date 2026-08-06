"""SQLAlchemy engine, session factory, and per-connection FK pragma."""
from typing import Dict
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """Enable foreign-key enforcement on every new SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Base class for ORM models (defined here so models can import it without
# creating circular imports through main.py)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Yield a database session and ensure it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health helper — returns a dict of {table_name: row_count}
# ---------------------------------------------------------------------------
_HEALTH_TABLES = [
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


def get_table_counts() -> Dict[str, int]:
    """Query row counts for all known tables."""
    counts: Dict[str, int] = {}
    with engine.connect() as conn:
        for table in _HEALTH_TABLES:
            row = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            counts[table] = row[0] if row else 0
    return counts
