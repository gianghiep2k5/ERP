# V-IMS AI Prototype — Role Permission Matrix (RBAC)

This document specifies the backend-enforced Role-Based Access Control (RBAC) rules for the V-IMS AI prototype codebase. All authorization constraints are strictly enforced at the FastAPI router dependency layer using reusable role guards (`require_role(...)`).

---

## 1. User Roles & Seed Credentials

| Role Name | Username | Password (Demo) | Primary Responsibility |
|---|---|---|---|
| **Warehouse Manager** | `warehouse.manager` | `Demo@123` | Decision-maker for approving, rejecting, or modifying recommended quantities. |
| **Planner** | `planner` | `Demo@123` | Demand forecasting reviewer, submits human feedback on AI baseline forecasts. |
| **Warehouse Staff** | `warehouse.staff` | `Demo@123` | Operational inventory visibility, stock tracking, and FEFO monitoring (Read-Only). |
| **Branch Manager** | `branch.manager` | `Demo@123` | Executive oversight across inventory, expiry risk, and recommendations (Read-Only). |
| **Quality Manager** | `quality.manager` | `Demo@123` | Quality assurance and shelf-life monitoring across lots and risk categories (Read-Only). |

---

## 2. API Endpoint Authorization Matrix

| API Endpoint | HTTP Method | Allowed Roles | Forbidden Roles (403) |
|---|---|---|---|
| **Auth & Diagnostics** | | | |
| `/api/health` | `GET` | *Public (No Token)* | None |
| `/api/auth/login` | `POST` | *Public (No Token)* | None |
| `/api/auth/me` | `GET` | All Authenticated | Unauthenticated (401) |
| **Dashboard & Core Inventory** | | | |
| `/api/dashboard/summary` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/inventory` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/inventory/{id}` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/lots` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/lots/{id}` | `GET` | All Authenticated | Unauthenticated (401) |
| **Explainable Expiry Risk** | | | |
| `/api/expiry-risk` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/expiry-risk/{lot_id}` | `GET` | All Authenticated | Unauthenticated (401) |
| **Demand Forecast & Planner Review** | | | |
| `/api/forecast/skus` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/forecast/{sku_id}` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/forecast/{sku_id}/review` | `POST` | **Planner Only** | Manager, Staff, Branch, Quality (403) |
| **Recommendations & Decision Workflow** | | | |
| `/api/recommendations` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/recommendations/{id}` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/recommendations/{id}/quantity` | `PATCH` | **Warehouse Manager Only** | Staff, Planner, Branch, Quality (403) |
| `/api/recommendations/{id}/approve` | `POST` | **Warehouse Manager Only** | Staff, Planner, Branch, Quality (403) |
| `/api/recommendations/{id}/reject` | `POST` | **Warehouse Manager Only** | Staff, Planner, Branch, Quality (403) |
| **Audit Logs** | | | |
| `/api/audit` | `GET` | All Authenticated | Unauthenticated (401) |
| `/api/audit/{id}` | `GET` | All Authenticated | Unauthenticated (401) |

---

## 3. Key RBAC Security Principles

1. **Strict Guard Enforcement**: Even if buttons are hidden or disabled in the React UI for non-authorized roles, all backend HTTP POST/PATCH routes validate JWT tokens and enforce role checks, returning HTTP `403 Forbidden` on unauthorized mutation attempts.
2. **Actor Traceability**: All audit entries and planner reviews extract `actor_username` / `reviewer_username` directly from the authenticated JWT token payload, never accepting user identity from request bodies.
3. **Double Processing Guard**: Approving, rejecting, or modifying non-`PENDING` recommendations returns HTTP `409 Conflict`.
4. **Password Hash Privacy**: Password hashes are stored securely using SHA-256 and are stripped from all API user serialization models.
