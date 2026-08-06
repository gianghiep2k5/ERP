"""Expiry Risk router: GET /api/expiry-risk and GET /api/expiry-risk/{lot_id}."""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import READ_ALL_ROLES, require_role
from app.models.user import User
from app.schemas.expiry_risk import (
    ExpiryRiskItem,
    ExpiryRiskListResponse,
    ExpiryRiskSummaryCounts,
)
from app.services.expiry_risk import fetch_all_expiry_assessments

router = APIRouter(prefix="/api/expiry-risk", tags=["expiry-risk"])

# Risk band severity ordering for sorting
SEVERITY_ORDER = {
    "Expired": 0,
    "Critical": 1,
    "High": 2,
    "Medium": 3,
    "Low": 4,
}


@router.get(
    "",
    response_model=ExpiryRiskListResponse,
    summary="List all inventory lots with explainable expiry risk scoring",
)
def list_expiry_risk(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    risk_band: Optional[str] = Query(None, description="Filter by risk band (Expired, Critical, High, Medium, Low)"),
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    expiry_bucket: Optional[str] = Query(None, description="Filter by expiry horizon (expired, <=30, 31-60, 61-90, >90)"),
    search: Optional[str] = Query(None, description="Search by SKU name or Lot ID"),
) -> ExpiryRiskListResponse:
    all_assessments = fetch_all_expiry_assessments(db)

    # Compute overall summary metrics across ALL 120 lots (unfiltered)
    expired_cnt = sum(1 for a in all_assessments if a.risk_band == "Expired")
    critical_cnt = sum(1 for a in all_assessments if a.risk_band == "Critical")
    high_cnt = sum(1 for a in all_assessments if a.risk_band == "High")
    medium_cnt = sum(1 for a in all_assessments if a.risk_band == "Medium")
    low_cnt = sum(1 for a in all_assessments if a.risk_band == "Low")
    total_surplus = round(sum(a.projected_surplus for a in all_assessments), 2)

    summary = ExpiryRiskSummaryCounts(
        expired_count=expired_cnt,
        critical_count=critical_cnt,
        high_count=high_cnt,
        medium_count=medium_cnt,
        low_count=low_cnt,
        total_projected_surplus=total_surplus,
    )

    # Apply filters
    filtered = all_assessments

    if risk_band:
        filtered = [a for a in filtered if a.risk_band.lower() == risk_band.lower()]
    if sku_id:
        filtered = [a for a in filtered if a.sku_id.lower() == sku_id.lower()]
    if category:
        filtered = [a for a in filtered if a.category.lower() == category.lower()]
    if location_id:
        filtered = [a for a in filtered if a.location_id.lower() == location_id.lower()]
    if expiry_bucket:
        eb = expiry_bucket.lower()
        if eb == "expired":
            filtered = [a for a in filtered if a.days_to_expiry <= 0]
        elif eb == "<=30":
            filtered = [a for a in filtered if 0 < a.days_to_expiry <= 30]
        elif eb == "31-60":
            filtered = [a for a in filtered if 30 < a.days_to_expiry <= 60]
        elif eb == "61-90":
            filtered = [a for a in filtered if 60 < a.days_to_expiry <= 90]
        elif eb == ">90":
            filtered = [a for a in filtered if a.days_to_expiry > 90]

    if search:
        s = search.lower()
        filtered = [
            a for a in filtered
            if s in a.sku_name.lower() or s in a.lot_id.lower() or s in a.sku_id.lower()
        ]

    # Sort: Severity desc (0=Expired, 1=Critical, ...), Risk Score desc, Expiry Date asc, Projected Surplus desc
    filtered.sort(
        key=lambda a: (
            SEVERITY_ORDER.get(a.risk_band, 99),
            -a.risk_score,
            a.expiry_date,
            -a.projected_surplus,
        )
    )

    items = [
        ExpiryRiskItem(
            inventory_id=a.inventory_id,
            lot_id=a.lot_id,
            sku_id=a.sku_id,
            sku_name=a.sku_name,
            category=a.category,
            location_id=a.location_id,
            location_name=a.location_name,
            available_qty=a.available_qty,
            on_hand_qty=a.on_hand_qty,
            manufacturing_date=a.manufacturing_date,
            expiry_date=a.expiry_date,
            analysis_date=a.analysis_date,
            days_to_expiry=a.days_to_expiry,
            recent_30d_sales_qty=a.recent_30d_sales_qty,
            recent_average_daily_demand=a.recent_average_daily_demand,
            forecast_consumption_before_expiry=a.forecast_consumption_before_expiry,
            forecast_method=a.forecast_method,
            projected_surplus=a.projected_surplus,
            projected_shortage=a.projected_shortage,
            surplus_ratio=a.surplus_ratio,
            urgency_factor=a.urgency_factor,
            risk_score=a.risk_score,
            risk_band=a.risk_band,
            explanation=a.explanation,
            proposed_actions=a.proposed_actions,
            fefo_position=a.fefo_position,
            related_recommendation_ids=a.related_recommendation_ids,
            pack_size=a.pack_size,
            public_product_id=a.public_product_id,
            product_name=a.product_name,
            source_url=a.source_url,
        )
        for a in filtered
    ]

    return ExpiryRiskListResponse(
        items=items,
        total=len(items),
        summary=summary,
    )


@router.get(
    "/{lot_id}",
    response_model=ExpiryRiskItem,
    summary="Get single lot expiry risk assessment",
)
def get_lot_expiry_risk(
    lot_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> ExpiryRiskItem:
    all_assessments = fetch_all_expiry_assessments(db)
    found = next((a for a in all_assessments if a.lot_id.upper() == lot_id.upper()), None)
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lot '{lot_id}' not found",
        )

    return ExpiryRiskItem(
        inventory_id=found.inventory_id,
        lot_id=found.lot_id,
        sku_id=found.sku_id,
        sku_name=found.sku_name,
        category=found.category,
        location_id=found.location_id,
        location_name=found.location_name,
        available_qty=found.available_qty,
        on_hand_qty=found.on_hand_qty,
        manufacturing_date=found.manufacturing_date,
        expiry_date=found.expiry_date,
        analysis_date=found.analysis_date,
        days_to_expiry=found.days_to_expiry,
        recent_30d_sales_qty=found.recent_30d_sales_qty,
        recent_average_daily_demand=found.recent_average_daily_demand,
        forecast_consumption_before_expiry=found.forecast_consumption_before_expiry,
        forecast_method=found.forecast_method,
        projected_surplus=found.projected_surplus,
        projected_shortage=found.projected_shortage,
        surplus_ratio=found.surplus_ratio,
        urgency_factor=found.urgency_factor,
        risk_score=found.risk_score,
        risk_band=found.risk_band,
        explanation=found.explanation,
        proposed_actions=found.proposed_actions,
        fefo_position=found.fefo_position,
        related_recommendation_ids=found.related_recommendation_ids,
        pack_size=found.pack_size,
        public_product_id=found.public_product_id,
        product_name=found.product_name,
        source_url=found.source_url,
    )
