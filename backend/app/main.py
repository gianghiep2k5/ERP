"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import audit as audit_router
from app.routers import auth as auth_router
from app.routers import dashboard as dashboard_router
from app.routers import expiry_risk as expiry_risk_router
from app.routers import forecast as forecast_router
from app.routers import health as health_router
from app.routers import inventory as inventory_router
from app.routers import lots as lots_router
from app.routers import recommendations as recommendations_router


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hook
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Nothing to initialise in Phase 1; future phases will run DB migrations here.
    yield


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="V-IMS AI Demo API",
    description=(
        "Demonstration using public product master references and synthetic "
        "operational data — not actual Vinamilk operational data."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and its production build origin
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health_router.router)
app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(inventory_router.router)
app.include_router(lots_router.router)
app.include_router(expiry_risk_router.router)
app.include_router(forecast_router.router)
app.include_router(recommendations_router.router)
app.include_router(audit_router.router)
