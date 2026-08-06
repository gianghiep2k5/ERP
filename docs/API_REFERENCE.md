# V-IMS AI Prototype — API Reference

This document documents all 19 HTTP API endpoints exposed by the FastAPI backend server (`http://localhost:8000`).

---

## 1. Authentication & System Endpoints

### `GET /api/health`
- **Authentication**: None (Public)
- **Roles**: All
- **Response**: `{ status: "ok", timestamp: str, uptime_seconds: float, database: { connected: bool, path: str, tables: dict } }`

### `POST /api/auth/login`
- **Authentication**: None (Public)
- **Roles**: All
- **Request Body**: `{ username: str, password: str }`
- **Response**: `{ access_token: str, token_type: "bearer", user: { username: str, role: str, full_name: str } }`
- **Errors**: `401 Unauthorized` (Invalid credentials)

### `GET /api/auth/me`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: `{ username: str, role: str, full_name: str, email: str }`

---

## 2. Executive Dashboard & Inventory Endpoints

### `GET /api/dashboard/summary`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: `{ total_skus: int, total_lots: int, total_on_hand_qty: int, pending_recommendations_count: int, stockout_scenario_count: int, expiry_scenario_count: int, transfer_scenario_count: int, data_updated_at: str }`

### `GET /api/inventory`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Query Params**: `sku_id`, `category`, `scenario`, `location_id`, `expiry_bucket`, `search`
- **Response**: `{ items: List[InventoryListItem], total: int }`

### `GET /api/inventory/{inventory_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: Full inventory balance detail with joined SKU, Lot, and Location info.

### `GET /api/lots`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Query Params**: `sku_id`, `location_id`, `search`
- **Response**: `{ items: List[LotListItem], total: int }`

### `GET /api/lots/{lot_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: Full lot detail joined with SKU, Public Product master, Location, and Related Recommendations.

---

## 3. Explainable Expiry Risk Endpoints

### `GET /api/expiry-risk`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Query Params**: `risk_band`, `sku_id`, `category`, `search`
- **Response**: `{ items: List[ExpiryRiskItem], total: int }`

### `GET /api/expiry-risk/{lot_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: Detailed expiry risk score breakdown (Days to Expiry, Projected Surplus, Shortage, Risk Band, Recommended Actions).

---

## 4. Demand Forecast & Planner Review Endpoints

### `GET /api/forecast/skus`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: List of 30 SKUs with model metrics and latest review status.

### `GET /api/forecast/{sku_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: `{ sku_id: str, sku_name: str, model_name: str, wape: float, bias: float, actual_sales: List[SalesObs], forecast_results: List[FcstObs], latest_review: ReviewItem, review_history: List[ReviewItem] }`

### `POST /api/forecast/{sku_id}/review`
- **Authentication**: Bearer JWT Token
- **Roles**: **Planner Only**
- **Request Body**: `{ review_status: str, planner_comment: str }`
- **Response**: `{ review_id: str, forecast_run_id: str, reviewer_username: str, review_status: str, planner_comment: str, reviewed_at: str }`
- **Errors**: `403 Forbidden` (Non-Planner roles), `422 Unprocessable Content` (Blank comment)

---

## 5. Recommendation Workflow Endpoints

### `GET /api/recommendations`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Query Params**: `status`, `recommendation_type`, `sku_id`, `lot_id`, `search`
- **Response**: `{ items: List[RecListItem], total: int, summary: SummaryCounts }`

### `GET /api/recommendations/{recommendation_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: Joined recommendation detail with proposed, adjusted, and effective quantity, plus audit history.

### `PATCH /api/recommendations/{recommendation_id}/quantity`
- **Authentication**: Bearer JWT Token
- **Roles**: **Warehouse Manager Only**
- **Request Body**: `{ adjusted_qty: int, comment: str }`
- **Response**: Updated recommendation detail with new `MODIFIED` audit row.
- **Errors**: `403 Forbidden` (Non-Manager roles), `409 Conflict` (Already processed), `422 Unprocessable Content` (Blank comment or qty <= 0)

### `POST /api/recommendations/{recommendation_id}/approve`
- **Authentication**: Bearer JWT Token
- **Roles**: **Warehouse Manager Only**
- **Request Body**: `{ comment: str }`
- **Response**: Updated recommendation detail (`status: APPROVED`) with new `APPROVED` audit row.
- **Errors**: `403 Forbidden` (Non-Manager roles), `409 Conflict` (Already processed), `422 Unprocessable Content` (Blank comment)

### `POST /api/recommendations/{recommendation_id}/reject`
- **Authentication**: Bearer JWT Token
- **Roles**: **Warehouse Manager Only**
- **Request Body**: `{ comment: str }`
- **Response**: Updated recommendation detail (`status: REJECTED`) with new `REJECTED` audit row.
- **Errors**: `403 Forbidden` (Non-Manager roles), `409 Conflict` (Already processed), `422 Unprocessable Content` (Blank comment)

---

## 6. Audit Log Endpoints

### `GET /api/audit`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Query Params**: `recommendation_id`, `actor_username`, `action`, `start_date`, `end_date`
- **Response**: `{ items: List[AuditItem], total: int }` (Sorted by `action_timestamp` desc)

### `GET /api/audit/{audit_id}`
- **Authentication**: Bearer JWT Token
- **Roles**: All Authenticated Users
- **Response**: Single audit log entry detail.
