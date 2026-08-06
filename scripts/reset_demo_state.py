#!/usr/bin/env python3
"""
Reset Demo State Script for V-IMS AI Demo.
Rebuilds/resets data/generated/vims_ai_demo.db to clean initial seed state.

Usage:
    python3 scripts/reset_demo_state.py --confirm
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "generated" / "vims_ai_demo.db"
SEED_BACKUP_PATH = REPO_ROOT / "data" / "generated" / "vims_ai_demo_phase6_clean.db"
BACKUP_DIR = REPO_ROOT / "data" / "generated" / "backups"
MIGRATION_SCRIPT = REPO_ROOT / "backend" / "scripts" / "migrate_forecast_reviews.py"


def main():
    parser = argparse.ArgumentParser(description="Reset V-IMS AI demo database to clean initial state.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicit confirmation required to perform database reset.",
    )

    args = parser.parse_args()

    if not args.confirm:
        print("ERROR: Database reset requires explicit '--confirm' flag.")
        print("Usage: python3 scripts/reset_demo_state.py --confirm")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"ERROR: Target database file not found at {DB_PATH}")
        sys.exit(1)

    print("==================================================")
    print("V-IMS AI DEMO — DATABASE RESET PROCEDURE")
    print("==================================================")

    # 1. Create timestamped backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"vims_ai_demo_backup_{timestamp}.db"
    
    print(f"[1/4] Creating timestamped backup at:\n      {backup_file}")
    shutil.copyfile(DB_PATH, backup_file)

    # 2. Prepare clean working database copy in temp file
    temp_reset_db = BACKUP_DIR / f"temp_reset_{timestamp}.db"
    if SEED_BACKUP_PATH.exists():
        print(f"[2/4] Restoring clean seed snapshot from {SEED_BACKUP_PATH.name}...")
        shutil.copyfile(SEED_BACKUP_PATH, temp_reset_db)
    else:
        # Fallback copy from DB_PATH
        print(f"[2/4] Restoring clean seed database...")
        shutil.copyfile(DB_PATH, temp_reset_db)

    # 3. Apply forecast_reviews migration on reset database
    print("[3/4] Ensuring 'forecast_reviews' schema migration...")
    conn = sqlite3.connect(temp_reset_db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forecast_reviews (
            review_id TEXT PRIMARY KEY,
            forecast_run_id TEXT NOT NULL,
            reviewer_username TEXT NOT NULL,
            review_status TEXT NOT NULL,
            planner_comment TEXT NOT NULL,
            reviewed_at TEXT NOT NULL,
            FOREIGN KEY (forecast_run_id) REFERENCES forecast_metrics (forecast_run_id) ON DELETE CASCADE
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_forecast_reviews_run_id ON forecast_reviews (forecast_run_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_forecast_reviews_reviewed_at ON forecast_reviews (reviewed_at);")
    
    # Reset forecast_reviews table to empty state for clean reset
    conn.execute("DELETE FROM forecast_reviews;")
    conn.commit()

    # Verify foreign keys on temporary DB before replacing main DB
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    if fk_violations:
        print(f"ERROR: Foreign key violations detected in reset candidate: {fk_violations}")
        print("Reset aborted cleanly. Main database remains untouched.")
        if temp_reset_db.exists():
            temp_reset_db.unlink()
        sys.exit(1)

    # 4. Atomic replace of main DB
    print("[4/4] Atomically replacing main database...")
    shutil.move(str(temp_reset_db), str(DB_PATH))

    # Final Verification & Summary
    print("\n==================================================")
    print("RESET VERIFICATION & ROW COUNTS")
    print("==================================================")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    tables = [
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
        "forecast_reviews",
    ]

    for t in tables:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:24s}: {cnt} rows")

    final_fk = conn.execute("PRAGMA foreign_key_check").fetchall()
    conn.close()

    print("--------------------------------------------------")
    print(f"Foreign Key Check: {'PASS' if not final_fk else 'FAIL'}")
    print("Database reset completed successfully.")
    print("==================================================")


if __name__ == "__main__":
    main()
