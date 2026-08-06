# V-IMS AI Prototype — Phase 7 User Acceptance Testing (UAT) Script

This document details the User Acceptance Testing (UAT) test cases for Phase 7 validation across the V-IMS AI prototype application (Phases 2–6).

---

## Acceptance Test Suite Summary

| Test Case ID | Feature / Module | Scenario Description | Precondition | Pass/Fail |
|---|---|---|---|---|
| **UAT-SEC-01** | Authentication | Valid Login as Warehouse Manager (`warehouse.manager` / `Demo@123`) | DB seeded | **PASS** |
| **UAT-SEC-02** | Authentication | Unauthenticated API Access returns `401 Unauthorized` | No JWT Token | **PASS** |
| **UAT-SEC-03** | RBAC Enforcement | Non-Manager role mutation returns `403 Forbidden` | Logged in as Staff/Planner | **PASS** |
| **UAT-DASH-01** | Dashboard | Summary metric aggregation from SQLite (`30` SKUs, `120` Lots, `18` Pending) | Authenticated | **PASS** |
| **UAT-INV-01** | Inventory & FEFO | Sort inventory by days to expiry & FEFO priority order | Authenticated | **PASS** |
| **UAT-LOT-01** | Lot Detail | Joined lot detail resolves SKU, location, balances, and recommendations | Authenticated | **PASS** |
| **UAT-RISK-01** | Expiry Risk | 8-formula calculation engine computes Days to Expiry & Projected Surplus | Analysis Date = 2026-08-05 | **PASS** |
| **UAT-RISK-02** | Expiry Risk | Risk band priority classification (`Critical`, `High`, `Medium`, `Low`) | Analysis Date = 2026-08-05 | **PASS** |
| **UAT-FCST-01** | Demand Forecast | Trajectory chart displays 365d actuals + 30d forecast without overlap | Analysis Date = 2026-08-05 | **PASS** |
| **UAT-FCST-02** | Demand Forecast | Planner role submits persistent Planner Review comment & status | Logged in as Planner | **PASS** |
| **UAT-FCST-03** | Demand Forecast | Non-Planner role cannot submit Planner Review (`403 Forbidden`) | Logged in as Manager | **PASS** |
| **UAT-REC-01** | Recommendations | List recommendations with summary counts (`PENDING`, `APPROVED`, `REJECTED`) | Authenticated | **PASS** |
| **UAT-REC-02** | Recommendations | Warehouse Manager modifies quantity (`PATCH /quantity`) | Logged in as Manager | **PASS** |
| **UAT-REC-03** | Recommendations | Warehouse Manager approves proposal (`POST /approve`) | Logged in as Manager | **PASS** |
| **UAT-REC-04** | Recommendations | Re-processing non-PENDING recommendation returns `409 Conflict` | Status != PENDING | **PASS** |
| **UAT-AUD-01** | Audit Log | Audit ID generation uses MAX numeric suffix (`AUD0039` ...) | Manager mutation done | **PASS** |
| **UAT-INTEG-01**| Database Integrity| Core tables (`inventory_balances`, `lots`, `sales_history`) remain unmodified | Post scenario execution | **PASS** |
| **UAT-RESET-01**| Demo Reset | `reset_demo_state.py --confirm` restores initial seed DB state | Backup created | **PASS** |

---

## Detailed Test Case Executions

### UAT-SCENARIO-1: Expiry Risk to Recommendation Approval Workflow (Dynamic Candidate Selection)

- **Precondition**: `vims_ai_demo.db` loaded; analysis date = `2026-08-05`.
- **Steps**:
  1. Authenticate as `warehouse.manager`.
  2. GET `/api/expiry-risk`. Inspect Critical expiry-risk lots (falling back to High if needed) to dynamically select an eligible lot (e.g. `LOT0073`, `Critical` Risk, Days to Expiry = `23`).
  3. GET `/api/recommendations?lot_id=LOT0073&status=PENDING`. Retrieve the matching PENDING recommendation (e.g. `REC0027`, `EXPIRY_ACTION`, `proposed_qty` = `867`). Verify `recommendation.lot_id == expiry_risk.lot_id`.
  4. PATCH `/api/recommendations/REC0027/quantity` with `adjusted_qty` = `767` and mandatory comment.
  5. Verify `proposed_qty` remains `867`, `adjusted_qty` becomes `767`, `effective_qty` becomes `767`, status remains `PENDING`, audit row `MODIFIED` exists.
  6. POST `/api/recommendations/REC0027/approve` with mandatory comment.
  7. Verify status becomes `APPROVED`, audit row `APPROVED` exists with `actor_username` = `warehouse.manager`.
  8. Verify `inventory_balances` count and contents remain 100% unchanged.
- **Expected Result**: Dynamic selection identifies matching Lot-Recommendation pair; approval workflow succeeds without modifying inventory balances.
- **Actual Result**: **PASS** (Verified by `test_phase7_scenarios.py`).

---

### UAT-SCENARIO-2: Demand Forecast & Planner Review Workflow

- **Precondition**: `vims_ai_demo.db` loaded.
- **Steps**:
  1. Authenticate as `planner`.
  2. GET `/api/forecast/SKU001`. Verify `365` actual observations (ending `2026-08-05`), `30` forecast observations (starting `2026-08-06`), WAPE = `0.1247`, Bias = `-0.0431`.
  3. POST `/api/forecast/SKU001/review` with status `ACCEPTED_AS_BASELINE` and comment `"Baseline validated"`.
  4. Verify review persists in `forecast_reviews`.
  5. Verify `forecast_results` and `forecast_metrics` remain 100% unchanged.
  6. Authenticate as `warehouse.manager` and POST review to `/api/forecast/SKU001/review`. Verify `403 Forbidden`.
- **Expected Result**: Planner review succeeds, manager receives 403, baseline model tables remain unchanged.
- **Actual Result**: **PASS** (Verified by `test_phase7_scenarios.py`).

---

### UAT-SCENARIO-3: Transfer Recommendation Decision Support

- **Precondition**: `vims_ai_demo.db` loaded.
- **Steps**:
  1. Authenticate as `warehouse.manager`.
  2. GET `/api/recommendations` filtered by type `TRANSFER` and status `PENDING`.
  3. Select PENDING transfer recommendation (e.g. `REC0011`). Verify source location, target location, and proposed quantity.
  4. Approve transfer recommendation with mandatory comment.
  5. Verify status changes to `APPROVED`, `APPROVED` audit entry created.
  6. Verify `inventory_balances` remains unchanged; no physical stock transfer or transfer order is created.
- **Expected Result**: Decision-support approval logged cleanly without inventory side effects.
- **Actual Result**: **PASS** (Verified by `test_phase7_scenarios.py`).
