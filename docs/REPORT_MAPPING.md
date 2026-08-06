# V-IMS AI Prototype — Academic Report Evidence Mapping

This document maps the implementation artifacts, visual features, and analytical outputs of the V-IMS AI prototype to standard academic report chapters.

---

## Report Chapter Mapping Matrix

| Report Chapter | Prototype Module / Artifact | Key Evidence / Output Demonstrated |
|---|---|---|
| **1. Current Management Process & Problem Statement** | Dashboard (`/dashboard`) & Inventory (`/inventory`) | Visualizing inventory fragmentation across 3 locations (`LOC01`, `LOC02`, `LOC03`), static expiry risks, and stock allocation challenges. |
| **2. Proposed New System & Business Requirements** | Expiry Risk Centre (`/expiry-risk`) & Recommendations (`/recommendations`) | Demonstrating human-in-the-loop decision support, 8-formula expiry risk scoring, and mandatory audit logging. |
| **3. System Design & Architecture** | `docs/ARCHITECTURE.md`, `backend/app/main.py`, `frontend/src/App.tsx` | Decoupled React + FastAPI + SQLite architecture, REST API design, JWT auth, and non-transactional boundaries. |
| **4. Implementation & Module Execution** | Expiry Risk Engine (`expiry_risk.py`), Demand Forecast (`/forecast`), Recommendations (`recommendations.py`) | 365d actuals + 30d forecast trajectory charts, WAPE/Bias metrics, Planner reviews, and Managerial two-step approvals. |
| **5. Security & Role-Based Access Control** | `docs/ROLE_MATRIX.md`, `backend/app/dependencies.py` | Role-based authorization across 5 roles, SHA-256 password security, JWT payload validation, and HTTP 403 enforcement. |
| **6. Verification, Testing & Data Integrity** | `docs/TEST_REPORT.md`, `backend/tests/`, `scripts/final_validate.py` | 88 passing pytest unit/integration tests, zero foreign key violations, and 100% database fingerprint integrity. |
| **7. Benefits, ROI & Operational Impact** | Executive Summary KPI Cards & Audit Logs (`/audit`) | Quantifiable reduction in potential unsellable surplus, complete managerial decision auditability, and FEFO compliance. |
| **8. Conclusion & Future Roadmap** | Disclaimers & Known Limitations in `README.md` | Academic decision-support prototype boundaries, synthetic operational data disclaimer, and roadmap for Phase 8 completion. |
