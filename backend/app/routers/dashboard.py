"""Dashboard router: GET /api/dashboard/summary."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import DEMO_ANALYSIS_DATE
from app.database import get_db
from app.dependencies import READ_ALL_ROLES, require_role
from app.models.inventory_balance import InventoryBalance
from app.models.lot import Lot
from app.models.recommendation import Recommendation
from app.models.sku import SKU
from app.models.user import User
from app.schemas.dashboard import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get calculated KPI dashboard metrics",
)
def get_dashboard_summary(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummary:
    """
    Calculates summary metrics dynamically from SQLite:
    - total SKUs
    - total lots
    - total on-hand inventory quantity
    - pending recommendations
    - scenario counts (stockout, expiry, transfer, normal)
    - latest inventory update timestamp
    """
    total_skus = db.query(func.count(SKU.sku_id)).scalar() or 0
    total_lots = db.query(func.count(Lot.lot_id)).scalar() or 0
    
    total_on_hand_qty = db.query(func.sum(InventoryBalance.on_hand_qty)).scalar() or 0
    
    pending_recommendations = (
        db.query(func.count(Recommendation.recommendation_id))
        .filter(Recommendation.status == "PENDING")
        .scalar()
        or 0
    )
    
    # Scenario counts
    stockout_count = (
        db.query(func.count(InventoryBalance.inventory_id))
        .filter(InventoryBalance.scenario == "stockout")
        .scalar()
        or 0
    )
    expiry_count = (
        db.query(func.count(InventoryBalance.inventory_id))
        .filter(InventoryBalance.scenario == "expiry")
        .scalar()
        or 0
    )
    transfer_count = (
        db.query(func.count(InventoryBalance.inventory_id))
        .filter(InventoryBalance.scenario == "transfer")
        .scalar()
        or 0
    )
    normal_count = (
        db.query(func.count(InventoryBalance.inventory_id))
        .filter(InventoryBalance.scenario == "normal")
        .scalar()
        or 0
    )
    
    latest_update = db.query(func.max(InventoryBalance.last_updated)).scalar()

    return DashboardSummary(
        total_skus=total_skus,
        total_lots=total_lots,
        total_on_hand_qty=total_on_hand_qty,
        pending_recommendations=pending_recommendations,
        stockout_count=stockout_count,
        expiry_count=expiry_count,
        transfer_count=transfer_count,
        normal_count=normal_count,
        latest_update=latest_update,
        analysis_date=DEMO_ANALYSIS_DATE.isoformat(),
    )
