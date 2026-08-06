# Vinamilk Inventory Management System (V-IMS) AI Prototype

**Academic Decision-Support Prototype** — Advanced Inventory Management & Demand Forecasting System for Fast-Moving Consumer Goods (FMCG).

---

## 1. Executive Summary & Purpose

The **Vinamilk Inventory Management System (V-IMS) AI Prototype** is an academic decision-support application built to demonstrate human-in-the-loop inventory management, explainable expiry-risk scoring, and baseline demand forecasting.

> **Decision-Support Prototype Notice**:  
> *This system is a decision-support prototype using synthetic operational data and public product master references. It does NOT execute automated inventory balance transactions, physical stock transfers, or purchase orders.*

---

## 2. Core Capabilities & Scope

1. **Authentication & Role-Based Access Control (RBAC)**:
   - 5 distinct user roles: `Warehouse Manager`, `Planner`, `Warehouse Staff`, `Branch Manager`, `Quality Manager`.
   - JWT authentication (`HS256`) with SHA-256 password verification.
   - Reusable backend role guards (`require_role(...)`) enforcing strict authorization on mutation routes.
2. **Executive Dashboard**:
   - 8 live metrics calculated dynamically from SQLite (`30` SKUs, `120` Lots, `524,420` on-hand units, `18` Pending recommendations, and scenario counts).
3. **FEFO Inventory & Lot Detail**:
   - First-Expired, First-Out (FEFO) sorting, expiry bucket filters (`<30d`, `30-60d`, `60-90d`, `>90d`), and joined lot detail views.
4. **Explainable Expiry-Risk Scoring**:
   - 8-formula mathematical calculation engine comparing remaining shelf life against 30-day forecast demand to compute projected surplus, shortage, and risk bands (`Critical`, `High`, `Medium`, `Low`, `Expired`).
5. **Demand Forecast & Planner Review**:
   - Interactive SVG trajectory charts displaying **365 days of actual sales history** (`2025-08-06` to `2026-08-05`) and **30 days of baseline forecast** (`2026-08-06` to `2026-09-04`) with vertical boundary lines, WAPE, Bias, and persistent Planner feedback.
6. **Recommendation Workflow & Human-in-the-Loop Decisions**:
   - Two-step workflow for `REPLENISHMENT`, `TRANSFER`, and `EXPIRY_ACTION` proposals.
   - Quantity adjustment (`adjusted_qty`) and Approval/Rejection restricted to `Warehouse Manager`.
7. **Immutable Audit Trail**:
   - Every managerial action creates an immutable `audit_logs` entry in SQLite using `AUD%04d` sequential ID generation.

---

## 3. Technology Stack

- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, PyJWT, Pydantic v2, pytest.
- **Frontend**: React 18, TypeScript, Vite, Vanilla CSS design system (dark mode, glassmorphism, responsive UI).
- **Database**: SQLite 3 (`data/generated/vims_ai_demo.db`) with `PRAGMA foreign_keys = ON`.

---

## 4. Academic Snapshot Date

All calculations, days-to-expiry metrics, and forecast windows are anchored to the fixed academic snapshot date:
```python
DEMO_ANALYSIS_DATE = date(2026, 8, 5)
```

---

## 5. Demo Credentials

| Role | Username | Password | Access Rights |
|---|---|---|---|
| **Warehouse Manager** | `warehouse.manager` | `Demo@123` | Full decision review rights (Modify Qty, Approve, Reject). |
| **Planner** | `planner` | `Demo@123` | Forecast review & Planner feedback submission. |
| **Warehouse Staff** | `warehouse.staff` | `Demo@123` | Read-Only across all modules. |
| **Branch Manager** | `branch.manager` | `Demo@123` | Executive Read-Only oversight. |
| **Quality Manager** | `quality.manager` | `Demo@123` | Quality & shelf-life Read-Only monitoring. |

---

## 6. Quick Start & Execution

### Prerequisites
- Python 3.9+ with `venv`
- Node.js 18+ and `npm`

### Step 1: Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start FastAPI backend server (Port 8000)
uvicorn app.main:app --reload --port 8000
```

### Step 2: Frontend Setup
```bash
cd frontend
npm install

# Start Vite development server (Port 5173)
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

---

## 7. Database Reset & Verification Commands

```bash
# Verify database row counts & foreign keys:
python3 scripts/verify_database.py

# Perform deterministic clean database reset:
python3 scripts/reset_demo_state.py --confirm

# Run read-only readiness validation:
python3 scripts/final_validate.py

# Execute full pytest test suite (88 backend tests):
cd backend && pytest tests/ -v
```

---

## 8. Known Limitations

- **Decision Support Prototype**: Managerial approval logs an audit entry and updates recommendation status, but does not issue actual transport orders or ERP stock adjustments.
- **Pre-generated Forecast Models**: The baseline forecast displays pre-computed Seasonal Naive outputs from `forecast_results` and does not execute online ML model retraining.
