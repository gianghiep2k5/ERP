# ANTIGRAVITY PHASE PROMPTS

## Phase 0 — Audit
Read `.agents/rules/vims-ai-project.md`, `README_SETUP_MAC.md`, `DATA_GOVERNANCE.md` and all files under `data/`. Run `python3 scripts/verify_database.py`. Do not write application code. Produce architecture, folder structure, database table list, API endpoint list, route/page list, risks, and stop for review.

## Phase 1 — Scaffold
Create `frontend` with React + TypeScript + Vite and `backend` with FastAPI + SQLAlchemy. Connect only to `data/generated/vims_ai_demo.db`, add CORS, `.env.example`, `/api/health`, frontend health display, README commands. Run backend health test and frontend build.

## Phase 2 — Login and RBAC
Implement seeded-user login, local demo token, role-aware navigation, backend role checks, and tests proving Warehouse Staff cannot approve.

## Phase 3 — Dashboard and Inventory
Implement dashboard summary, inventory list, filters, lot detail, FEFO priority, and synthetic-data disclaimer. Verify in browser.

## Phase 4 — Expiry Risk
Implement explainable days-to-expiry, recent demand, forecast consumption before expiry, projected surplus, risk score/band, reasons and proposed actions. Test normal/medium/high-risk lots.

## Phase 5 — Forecast
Implement SKU selector, 12-month sales chart, 30-day forecast, WAPE, Bias, baseline label, and Planner review comment/status using existing forecast tables.

## Phase 6 — Recommendations and Audit
Implement list/detail, REPLENISHMENT/TRANSFER/EXPIRY_ACTION, approve/reject/modify quantity with reason, role checks, atomic update and audit log. Test permissions and audit trail.

## Phase 7 — Browser Verification
Run three flows: expiry approval, Planner forecast review, and transfer recommendation. Capture screenshots, test results, a 3-minute demo script, backup procedure and limitations.

## Phase 8 — Hardening
Run tests/build/foreign-key check, remove boilerplate, verify no false claims, and update startup README.
