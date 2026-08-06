# V-IMS AI Prototype — System Architecture Document

This document outlines the software architecture, data flow, security model, and human-in-the-loop decision boundaries for the Vinamilk Inventory Management System (V-IMS) AI Academic Prototype.

---

## 1. System Architecture Overview

V-IMS AI is structured as a decoupled, multi-tier web application consisting of:
1. **Frontend Presentation Tier**: React + TypeScript single-page application built with Vite and custom Vanilla CSS.
2. **Application & API Tier**: FastAPI REST backend providing authenticated API services, role guard dependencies, and analytical engines.
3. **Data Storage Tier**: Single embedded SQLite database (`data/generated/vims_ai_demo.db`) managed via SQLAlchemy ORM with foreign key enforcement (`PRAGMA foreign_keys = ON`).

```
+-------------------------------------------------------------------+
|                  React + TypeScript + Vite SPA                    |
|       (Dashboard, Inventory, Expiry Risk, Forecast, Recs, Audit)  |
+-------------------------------------------------------------------+
                                  |
                                  | REST HTTP + Bearer Token
                                  v
+-------------------------------------------------------------------+
|                        FastAPI Backend API                        |
|  +-------------------+  +-------------------+  +----------------+ |
|  | Auth & JWT Guard  |  | Expiry Risk Engine|  | Rec & Audit    | |
|  +-------------------+  +-------------------+  +----------------+ |
+-------------------------------------------------------------------+
                                  |
                                  | SQLAlchemy ORM
                                  v
+-------------------------------------------------------------------+
|                     SQLite 3 Embedded Database                    |
|             (data/generated/vims_ai_demo.db - 12 Tables)         |
+-------------------------------------------------------------------+
```

---

## 2. Core Architectural Layers

### 2.1 Backend Architecture (FastAPI + SQLAlchemy)
- **`backend/app/main.py`**: Entry point configuring CORS middleware (restricted to `http://localhost:5173`), lifespan hooks, and router registrations.
- **`backend/app/config.py`**: Settings manager reading environment variables via `pydantic-settings`. Computes absolute path to `vims_ai_demo.db`.
- **`backend/app/database.py`**: SQLAlchemy engine configuration enforcing `PRAGMA foreign_keys = ON` on every SQLite connection.
- **`backend/app/auth.py`**: Cryptographic module for SHA-256 password verification and PyJWT token generation (`HS256`).
- **`backend/app/dependencies.py`**: Dependency injection layer evaluating `Authorization: Bearer <token>` and enforcing role permissions (`require_role(...)`).
- **`backend/app/services/expiry_risk.py`**: Mathematical calculation engine executing all 8 expiry-risk scoring formulas and risk band priorities.

### 2.2 Frontend Architecture (React + TypeScript + Vite)
- **`frontend/src/api/client.ts`**: Axios instance managing request interception (attaching Bearer JWT tokens from `localStorage["vims_token"]`) and global HTTP 401 handling.
- **`frontend/src/auth/AuthContext.tsx`**: Context provider tracking current user state, token decoding, and role helper getters (`canApprove`, `isPlanner`).
- **`frontend/src/auth/RequireAuth.tsx`**: Route guard checking authentication before rendering protected layouts (`AppShell`).

---

## 3. Human-in-the-Loop & Decision Boundaries

V-IMS AI strictly separates decision support from physical execution:

```
[ System Proposal ]  -->  [ Manager Review ]  -->  [ Qty Adjustment ]  -->  [ Approve / Reject ]  -->  [ Audit Log ]
                                                                                                           (No Inventory Balance Change)
```

1. **System Proposals**: AI algorithms generate recommendations (`REPLENISHMENT`, `TRANSFER`, `EXPIRY_ACTION`) with a `proposed_qty`.
2. **Managerial Control**: Only `Warehouse Manager` can modify quantity (`adjusted_qty`) or approve/reject proposals.
3. **Effective Quantity Calculation**:
   $$\text{effective\_qty} = \text{COALESCE}(\text{adjusted\_qty}, \text{proposed\_qty})$$
4. **Immutable Audit Trail**: Approvals and modifications generate an `AUD%04d` entry in `audit_logs`.
5. **Non-Transaction Boundary**: Approvals log decisions for management review, but **do not alter `inventory_balances` or generate purchase orders**.

---

## 4. Analytical Flow & Expiry Risk Engine

Expiry risk scoring combines remaining shelf life with expected sales demand:

1. **Days to Expiry**:
   $$\text{days\_to\_expiry} = \text{expiry\_date} - \text{DEMO\_ANALYSIS\_DATE}$$
2. **Projected Consumption**:
   $$\text{projected\_consumption} = \text{days\_to\_expiry} \times \text{recent\_average\_daily\_demand}$$
3. **Projected Surplus**:
   $$\text{projected\_surplus} = \max(0, \text{available\_quantity} - \text{projected\_consumption})$$
4. **Risk Classification**:
   - `Expired` ($\text{days\_to\_expiry} \le 0$)
   - `Critical` ($\text{days\_to\_expiry} \le 30 \land \text{projected\_surplus} > 0$)
   - `High` ($\text{days\_to\_expiry} \le 60 \land \text{projected\_surplus} > 0$)
   - `Medium` ($\text{days\_to\_expiry} \le 90$)
   - `Low` ($\text{days\_to\_expiry} > 90$)
