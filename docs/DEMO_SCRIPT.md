# V-IMS AI Prototype — Demonstration Script (10–12 Minutes)

This demonstration script guides presenters through an interactive presentation of the Vinamilk Inventory Management System (V-IMS) AI decision-support prototype.

> **Important Decision-Support Notice**:  
> *"This prototype provides human-in-the-loop decision support and does not execute physical stock transactions, purchase orders, or automatic inventory balance adjustments."*

---

## Demo Agenda (10–12 Minutes Total)

| Step | Time | Module / Feature | Key Message / Action |
|---|---|---|---|
| 1 | 01:00 | **Authentication & System Login** | Log in as `warehouse.manager`. Showcase role-based welcome & navigation bar. |
| 2 | 01:30 | **Executive Dashboard Overview** | Review 8 live SQLite metrics (Total SKUs, Total Lots, Total On-Hand, Pending Recs, Risk scenario counts). |
| 3 | 01:30 | **Inventory & FEFO Priority** | Search & filter inventory by FEFO priority bucket, SKU, and location (`LOC01`, `LOC02`, `LOC03`). |
| 4 | 02:00 | **Explainable Expiry Risk Centre** | Open `/expiry-risk/LOT0073` (Critical Risk). Explain formula breakdown (Days to Expiry, Projected Surplus, Risk Score). |
| 5 | 02:00 | **Demand Forecast & Planner Review** | Switch user to `planner`. View 365d actuals + 30d forecast trajectory for `SKU001`. Submit Planner Review. |
| 6 | 02:30 | **Recommendation Modify & Approve** | Logged in as `warehouse.manager`. Open matching recommendation `/recommendations/REC0027`. Modify quantity & Approve with mandatory comment. |
| 7 | 01:30 | **Immutable Audit Trail** | Navigate to `/audit`. View `MODIFIED` and `APPROVED` entries for `REC0027` proving full traceability. |
| 8 | 00:30 | **Wrap-Up & Non-Transaction Disclaimer** | Reiterate decision-support prototype boundaries. |

---

## Detailed Step-by-Step Walkthrough

### Step 1: Authentication & System Login (1:00)
- **URL**: `http://localhost:5173/login`
- **Action**: Enter username `warehouse.manager` and password `Demo@123`.
- **Narration**: *"V-IMS AI features role-based access control. Logging in as Warehouse Manager grants full decision review rights over replenishment, transfer, and expiry action recommendations."*

### Step 2: Executive Dashboard (1:30)
- **URL**: `http://localhost:5173/dashboard`
- **Action**: Highlight the 8 metric cards computed dynamically from SQLite:
  - Total SKUs: `30`
  - Total Lots: `120`
  - Total On-hand Qty: `524,420` units
  - Pending Recommendations: `18`
  - Stock-out / Expiry / Transfer Scenario counts
- **Narration**: *"The executive dashboard provides real-time visibility across all 30 Vinamilk SKUs and 120 inventory balances."*

### Step 3: Inventory List & FEFO Priority (1:30)
- **URL**: `http://localhost:5173/inventory`
- **Action**: Filter by Expiry Bucket `< 30 Days`. Click on lot `LOT0073` (*Fresh Milk 100% Strawberry*).
- **Narration**: *"V-IMS tracks inventory using First-Expired, First-Out (FEFO) rules. Clicking LOT0073 displays full product master data, manufacturing date, expiry date, and days to expiry."*

### Step 4: Explainable Expiry Risk Centre (2:00)
- **URL**: `http://localhost:5173/expiry-risk/LOT0073`
- **Action**: Show the Expiry Risk score (`Critical` Risk, `23` Days to Expiry), and Projected Surplus.
- **Narration**: *"Unlike traditional FEFO which only considers dates, V-IMS compares remaining shelf life against 30-day forecast demand to project unsellable surplus before expiry. Clicking 'Review Recommendation' links directly to the pending action proposal REC0027."*

### Step 5: Demand Forecast & Planner Review (2:00)
- **URL**: `http://localhost:5173/forecast` (Logged in as `planner`)
- **Action**: Select `SKU001`. Point out:
  - 365 days of solid indigo actual sales history (ending `2026-08-05`).
  - Vertical sky-blue boundary line labeled `"Forecast begins: 2026-08-06"`.
  - 30 days of dashed green baseline forecast.
  - KPI Cards: Forecast WAPE (`12.47%`), Forecast Bias (`-4.31%`).
  - Select status `ACCEPTED_AS_BASELINE`, enter comment `"Verified against promotional calendar."`, and click **Save Planner Review**.
- **Narration**: *"Planners can review trajectory charts and document human feedback without altering baseline models."*

### Step 6: Recommendation Modify & Approve (2:30)
- **URL**: `http://localhost:5173/recommendations/REC0027` (Logged in as `warehouse.manager`)
- **Action**:
  1. Verify matching `lot_id` (`LOT0073`).
  2. Click **Modify Quantity**, change quantity from `867` to `767` with comment `"Adjusted down due to local promotion allocation."` -> Confirm modal.
  3. Click **Approve Proposal**, enter comment `"Approved effective quantity for immediate action."` -> Confirm modal.
- **Narration**: *"Warehouse Managers review AI recommendations for the matching lot, adjust quantities if required, and approve proposals using a clear two-step workflow."*

### Step 7: Immutable Audit Trail (1:30)
- **URL**: `http://localhost:5173/audit`
- **Action**: Show newly appended `MODIFIED` and `APPROVED` audit rows for `REC0027` with actor `warehouse.manager`, timestamp, and rationale.
- **Narration**: *"Every managerial action is immutably logged in SQLite with full status transition history."*

### Step 8: Wrap-Up & Disclaimer (0:30)
- **Narration**: *"This completes the V-IMS AI Phase 7 acceptance review. All decision workflows have been verified."*
