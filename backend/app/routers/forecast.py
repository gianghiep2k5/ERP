"""Forecast router: GET /api/forecast/skus, GET /api/forecast/{sku_id}, POST /api/forecast/{sku_id}/review."""
from datetime import datetime
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import DEMO_ANALYSIS_DATE
from app.database import get_db
from app.dependencies import PLANNER_ROLES, READ_ALL_ROLES, require_role
from app.models.forecast_metric import ForecastMetric
from app.models.forecast_result import ForecastResult
from app.models.forecast_review import ForecastReview
from app.models.sales_history import SalesHistory
from app.models.sku import SKU
from app.models.user import User
from app.schemas.forecast import (
    CreateReviewRequest,
    ForecastObservation,
    ForecastSKUDetailResponse,
    ForecastSKUListItem,
    ReviewItem,
    SalesObservation,
)

router = APIRouter(prefix="/api/forecast", tags=["forecast"])

ALLOWED_REVIEW_STATUSES = {
    "ACCEPTED_AS_BASELINE",
    "ADJUSTMENT_REQUIRED",
    "MONITOR",
}


@router.get(
    "/skus",
    response_model=List[ForecastSKUListItem],
    summary="List all 30 SKUs with forecast baseline metrics and review status",
)
def list_forecast_skus(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> List[ForecastSKUListItem]:
    """Returns list of SKUs with associated forecast metrics and latest review status."""
    results = (
        db.query(SKU, ForecastMetric)
        .join(ForecastMetric, SKU.sku_id == ForecastMetric.sku_id)
        .order_by(SKU.sku_id.asc())
        .all()
    )

    items: List[ForecastSKUListItem] = []
    for sku, metric in results:
        # Fetch latest review for this forecast_run_id if exists
        latest_rev = (
            db.query(ForecastReview)
            .filter(ForecastReview.forecast_run_id == metric.forecast_run_id)
            .order_by(ForecastReview.reviewed_at.desc())
            .first()
        )

        items.append(
            ForecastSKUListItem(
                sku_id=sku.sku_id,
                sku_name=sku.sku_name,
                category=sku.category,
                forecast_run_id=metric.forecast_run_id,
                wape=metric.wape,
                bias=metric.bias,
                model_name=metric.model_name,
                review_status=latest_rev.review_status if latest_rev else None,
            )
        )

    return items


@router.get(
    "/{sku_id}",
    response_model=ForecastSKUDetailResponse,
    summary="Get 12-month actual sales history and 30-day forecast observations for SKU",
)
def get_forecast_sku_detail(
    sku_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> ForecastSKUDetailResponse:
    """Returns 365 actual sales history observations and 30 forecast observations for a SKU."""
    sku_metric = (
        db.query(SKU, ForecastMetric)
        .join(ForecastMetric, SKU.sku_id == ForecastMetric.sku_id)
        .filter(SKU.sku_id == sku_id.upper())
        .first()
    )

    if not sku_metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU '{sku_id}' with forecast metrics not found",
        )

    sku, metric = sku_metric

    # 1. Fetch 365 actual sales history observations ending on 2026-08-05
    sales_rows = (
        db.query(
            SalesHistory.sales_date,
            func.sum(SalesHistory.quantity_sold).label("total_qty"),
        )
        .filter(SalesHistory.sku_id == sku.sku_id)
        .group_by(SalesHistory.sales_date)
        .order_by(SalesHistory.sales_date.asc())
        .all()
    )

    actual_sales = [
        SalesObservation(sales_date=s_date, quantity_sold=qty)
        for s_date, qty in sales_rows
    ]

    actual_start = actual_sales[0].sales_date if actual_sales else ""
    actual_end = actual_sales[-1].sales_date if actual_sales else ""

    # 2. Fetch 30 forecast observations starting after 2026-08-05
    forecast_rows = (
        db.query(ForecastResult.forecast_date, ForecastResult.forecast_qty)
        .filter(ForecastResult.forecast_run_id == metric.forecast_run_id)
        .order_by(ForecastResult.forecast_date.asc())
        .all()
    )

    forecast_results = [
        ForecastObservation(forecast_date=f_date, forecast_qty=qty)
        for f_date, qty in forecast_rows
    ]

    forecast_start = forecast_results[0].forecast_date if forecast_results else ""
    forecast_end = forecast_results[-1].forecast_date if forecast_results else ""

    # 3. Fetch review history
    reviews_rows = (
        db.query(ForecastReview)
        .filter(ForecastReview.forecast_run_id == metric.forecast_run_id)
        .order_by(ForecastReview.reviewed_at.desc())
        .all()
    )

    review_history = [
        ReviewItem(
            review_id=r.review_id,
            forecast_run_id=r.forecast_run_id,
            reviewer_username=r.reviewer_username,
            review_status=r.review_status,
            planner_comment=r.planner_comment,
            reviewed_at=r.reviewed_at,
        )
        for r in reviews_rows
    ]

    latest_review = review_history[0] if review_history else None

    return ForecastSKUDetailResponse(
        sku_id=sku.sku_id,
        sku_name=sku.sku_name,
        category=sku.category,
        analysis_date=DEMO_ANALYSIS_DATE.isoformat(),
        actual_start_date=actual_start,
        actual_end_date=actual_end,
        actual_sales=actual_sales,
        forecast_start_date=forecast_start,
        forecast_end_date=forecast_end,
        forecast_results=forecast_results,
        forecast_run_id=metric.forecast_run_id,
        model_name=metric.model_name,
        wape=metric.wape,
        bias=metric.bias,
        evaluation_window_days=metric.evaluation_window_days,
        latest_review=latest_review,
        review_history=review_history,
    )


@router.post(
    "/{sku_id}/review",
    response_model=ReviewItem,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a Planner review for a forecast baseline (Planner role only)",
)
def create_forecast_review(
    sku_id: str,
    body: CreateReviewRequest,
    current_user: Annotated[User, Depends(require_role(PLANNER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> ReviewItem:
    """
    Submits a new Planner review for the forecast baseline.
    Requires Planner role. Mandatory non-blank planner_comment.
    """
    # 1. Validate comment
    comment_text = body.planner_comment.strip() if body.planner_comment else ""
    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Planner comment is mandatory and cannot be blank.",
        )

    # 2. Validate review status
    if body.review_status not in ALLOWED_REVIEW_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid review_status '{body.review_status}'. Allowed: {sorted(ALLOWED_REVIEW_STATUSES)}",
        )

    # 3. Resolve metric/run_id for SKU
    metric = (
        db.query(ForecastMetric)
        .filter(ForecastMetric.sku_id == sku_id.upper())
        .first()
    )

    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU '{sku_id}' not found or has no forecast run",
        )

    # 4. Create new persistent review record
    review_id = f"REV-{uuid.uuid4().hex[:8]}"
    reviewed_at = datetime.utcnow().isoformat()

    review = ForecastReview(
        review_id=review_id,
        forecast_run_id=metric.forecast_run_id,
        reviewer_username=current_user.username,
        review_status=body.review_status,
        planner_comment=comment_text,
        reviewed_at=reviewed_at,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return ReviewItem(
        review_id=review.review_id,
        forecast_run_id=review.forecast_run_id,
        reviewer_username=review.reviewer_username,
        review_status=review.review_status,
        planner_comment=review.planner_comment,
        reviewed_at=review.reviewed_at,
    )
