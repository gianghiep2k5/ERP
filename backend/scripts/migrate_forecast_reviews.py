"""Idempotent migration script to create the forecast_reviews table in vims_ai_demo.db.

Schema:
- review_id TEXT PRIMARY KEY
- forecast_run_id TEXT NOT NULL (FK -> forecast_metrics.forecast_run_id)
- reviewer_username TEXT NOT NULL
- review_status TEXT NOT NULL (ACCEPTED_AS_BASELINE, ADJUSTMENT_REQUIRED, MONITOR)
- planner_comment TEXT NOT NULL
- reviewed_at TEXT NOT NULL (ISO datetime)

Indices:
- idx_forecast_reviews_run_id
- idx_forecast_reviews_reviewed_at
"""
from pathlib import Path
import sqlite3
import sys

# Locate database relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "generated" / "vims_ai_demo.db"


def run_migration(db_path: Path = DB_PATH) -> bool:
    if not db_path.exists():
        print(f"Error: Database file not found at {db_path}", file=sys.stderr)
        return False

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    # Check if forecast_reviews already exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='forecast_reviews'"
    ).fetchone()

    already_existed = table_check is not None

    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forecast_reviews (
            review_id TEXT PRIMARY KEY,
            forecast_run_id TEXT NOT NULL,
            reviewer_username TEXT NOT NULL,
            review_status TEXT NOT NULL,
            planner_comment TEXT NOT NULL,
            reviewed_at TEXT NOT NULL,
            FOREIGN KEY (forecast_run_id) REFERENCES forecast_metrics (forecast_run_id) ON DELETE CASCADE
        )
    """)

    # Create indices if not exist
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecast_reviews_run_id
        ON forecast_reviews (forecast_run_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_forecast_reviews_reviewed_at
        ON forecast_reviews (reviewed_at)
    """)

    conn.commit()

    # Verify foreign key integrity
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    if fk_check:
        print(f"Error: Foreign key check failed after migration: {fk_check}", file=sys.stderr)
        return False

    if already_existed:
        print(f"Migration completed: 'forecast_reviews' table already existed in {db_path.name}.")
    else:
        print(f"Migration completed: Successfully created 'forecast_reviews' table in {db_path.name}.")

    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
