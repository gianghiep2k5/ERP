from pathlib import Path
import sqlite3
db=Path(__file__).resolve().parents[1]/"data/generated/vims_ai_demo.db"
conn=sqlite3.connect(db); conn.execute("PRAGMA foreign_keys=ON")
for t in ["public_products","skus","locations","users","lots","inventory_balances","sales_history","forecast_metrics","forecast_results","recommendations","audit_logs"]:
 print(f"{t:24s}",conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
print("Foreign-key check:","PASS" if not conn.execute("PRAGMA foreign_key_check").fetchall() else "FAIL")
for r in conn.execute("SELECT recommendation_id,recommendation_type,sku_id,proposed_qty,status FROM recommendations LIMIT 10"): print(r)
conn.close()
