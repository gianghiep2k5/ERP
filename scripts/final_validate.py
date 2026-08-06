#!/usr/bin/env python3
"""
Final Validation Script for V-IMS AI Academic Prototype (Phase 8).
Read-only validation script verifying database integrity, schema rules,
date ranges, required files, role mappings, and documentation readiness.

Usage:
    python3 scripts/final_validate.py
"""
import os
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# Repository Root
REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = REPO_ROOT / "data" / "generated" / "vims_ai_demo.db"
DEMO_ANALYSIS_DATE = date(2026, 8, 5)

REQUIRED_FILES = [
    # Core Application Files
    REPO_ROOT / "data" / "generated" / "vims_ai_demo.db",
    REPO_ROOT / "scripts" / "verify_database.py",
    REPO_ROOT / "scripts" / "reset_demo_state.py",
    REPO_ROOT / "backend" / "app" / "main.py",
    REPO_ROOT / "backend" / "app" / "config.py",
    REPO_ROOT / "backend" / "app" / "auth.py",
    REPO_ROOT / "frontend" / "src" / "App.tsx",
    REPO_ROOT / "frontend" / "package.json",
    # Documentation Set
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs" / "ARCHITECTURE.md",
    REPO_ROOT / "docs" / "API_REFERENCE.md",
    REPO_ROOT / "docs" / "DATA_DICTIONARY.md",
    REPO_ROOT / "docs" / "TEST_REPORT.md",
    REPO_ROOT / "docs" / "INSTALLATION.md",
    REPO_ROOT / "docs" / "PHASE7_UAT.md",
    REPO_ROOT / "docs" / "DEMO_SCRIPT.md",
    REPO_ROOT / "docs" / "ROLE_MATRIX.md",
    REPO_ROOT / "docs" / "SUBMISSION_CHECKLIST.md",
    REPO_ROOT / "docs" / "REPORT_MAPPING.md",
]

EXPECTED_TABLE_COUNTS = {
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
}

EXPECTED_USERS = {
    "warehouse.manager": "Warehouse Manager",
    "planner": "Planner",
    "warehouse.staff": "Warehouse Staff",
    "branch.manager": "Branch Manager",
    "quality.manager": "Quality Manager",
}


def run_validation():
    print("==================================================")
    print("V-IMS AI — FINAL READINESS & INTEGRITY VALIDATION")
    print("==================================================")
    passed_checks = 0
    total_checks = 0

    def check(description: str, condition: bool, failure_msg: str = ""):
        nonlocal passed_checks, total_checks
        total_checks += 1
        if condition:
            print(f"  [PASS] {description}")
            passed_checks += 1
            return True
        else:
            print(f"  [FAIL] {description} - {failure_msg}")
            return False

    # 1. Check Required Files
    print("\n--- 1. FILE EXISTENCE & STRUCTURE ---")
    all_files_exist = True
    for f_path in REQUIRED_FILES:
        rel_path = f_path.relative_to(REPO_ROOT)
        if not check(f"File exists: {rel_path}", f_path.exists(), "File missing!"):
            all_files_exist = False

    # 2. Database Connection & FK Check
    print("\n--- 2. DATABASE INTEGRITY & SCHEMA ---")
    db_accessible = DB_PATH.exists()
    check("SQLite database exists", db_accessible, f"Database not found at {DB_PATH}")

    if not db_accessible:
        print("\nFATAL: Database inaccessible. Stopping validation.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    check("Foreign key check (PRAGMA foreign_key_check)", len(fk_violations) == 0, f"Violations: {fk_violations}")

    # 3. Core Table Row Counts
    print("\n--- 3. TABLE ROW COUNTS ---")
    for tbl, exp_cnt in EXPECTED_TABLE_COUNTS.items():
        actual_cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        check(f"Table '{tbl}' row count == {exp_cnt}", actual_cnt == exp_cnt, f"Actual: {actual_cnt}")

    audit_cnt = conn.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
    check("Table 'audit_logs' row count >= 24", audit_cnt >= 24, f"Actual: {audit_cnt}")

    review_table_exists = conn.execute(
        "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='forecast_reviews'"
    ).fetchone()[0] == 1
    check("Table 'forecast_reviews' exists", review_table_exists, "Table missing!")

    # 4. User Roles & Security
    print("\n--- 4. USER ROLES & CREDENTIAL SECURITY ---")
    users = dict(conn.execute("SELECT username, role FROM users").fetchall())
    for uname, expected_role in EXPECTED_USERS.items():
        check(f"User '{uname}' exists with role '{expected_role}'", users.get(uname) == expected_role, f"Actual role: {users.get(uname)}")

    # Ensure password hashes are not exposed or printed
    sample_user = conn.execute("SELECT username, password_hash FROM users LIMIT 1").fetchone()
    check("User records contain non-empty password hashes", sample_user and len(sample_user[1]) > 0, "Empty password hash!")

    # 5. Data Relationships & Consistency
    print("\n--- 5. DATA RELATIONSHIP CONSISTENCY ---")
    # Verify LOT0009 is linked to REC0005 in seed dataset
    rec0005 = conn.execute("SELECT recommendation_id, lot_id, status FROM recommendations WHERE recommendation_id = 'REC0005'").fetchone()
    check("REC0005 belongs to LOT0009 (APPROVED)", rec0005 and rec0005[1] == "LOT0009" and rec0005[2] == "APPROVED", f"Actual: {rec0005}")

    # Check recommendation types
    rec_types = set(r[0] for r in conn.execute("SELECT DISTINCT recommendation_type FROM recommendations").fetchall())
    expected_types = {"REPLENISHMENT", "TRANSFER", "EXPIRY_ACTION"}
    check("All 3 recommendation types present", expected_types.issubset(rec_types), f"Actual types: {rec_types}")

    # 6. Date Range & Forecast Window
    print("\n--- 6. DATE RANGE & FORECAST WINDOW ---")
    max_sales_date = conn.execute("SELECT MAX(sales_date) FROM sales_history").fetchone()[0]
    check(f"Sales history ends on DEMO_ANALYSIS_DATE ({DEMO_ANALYSIS_DATE})", max_sales_date == str(DEMO_ANALYSIS_DATE), f"Actual: {max_sales_date}")

    min_forecast_date = conn.execute("SELECT MIN(forecast_date) FROM forecast_results").fetchone()[0]
    check("Forecast results start after analysis date (2026-08-06)", min_forecast_date == "2026-08-06", f"Actual: {min_forecast_date}")

    # Check observation counts for representative SKU001
    sku001_sales_cnt = conn.execute("SELECT COUNT(DISTINCT sales_date) FROM sales_history WHERE sku_id = 'SKU001'").fetchone()[0]
    check("SKU001 has 365 actual sales days", sku001_sales_cnt == 365, f"Actual: {sku001_sales_cnt}")

    sku001_fc_cnt = conn.execute("SELECT COUNT(DISTINCT forecast_date) FROM forecast_results WHERE sku_id = 'SKU001'").fetchone()[0]
    check("SKU001 has 30 forecast days", sku001_fc_cnt == 30, f"Actual: {sku001_fc_cnt}")

    conn.close()

    # Final Summary
    print("\n==================================================")
    print("FINAL VALIDATION SUMMARY")
    print("==================================================")
    print(f"Total Checks Executed : {total_checks}")
    print(f"Passed Checks         : {passed_checks}")
    print(f"Failed Checks         : {total_checks - passed_checks}")
    print("--------------------------------------------------")

    if passed_checks == total_checks:
        print("RESULT: ALL READINESS VALIDATION CHECKS PASSED (100% PASS) ✅")
        sys.exit(0)
    else:
        print("RESULT: VALIDATION FAILED ❌")
        sys.exit(1)


if __name__ == "__main__":
    run_validation()
