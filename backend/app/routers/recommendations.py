"""Recommendations router: GET /api/recommendations, GET /api/recommendations/{id}, PATCH quantity, POST approve, POST reject."""
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Integer, func
from sqlalchemy.orm import Session

from app.constants import DEMO_ANALYSIS_DATE
from app.database import get_db
from app.dependencies import APPROVER_ROLES, READ_ALL_ROLES, require_role
from app.models.audit_log import AuditLog
from app.models.location import Location
from app.models.lot import Lot
from app.models.recommendation import Recommendation
from app.models.sku import SKU
from app.models.user import User
from app.schemas.recommendation import (
    ApproveRecommendationRequest,
    ModifyQuantityRequest,
    RecommendationAuditItem,
    RecommendationDetailResponse,
    RecommendationListItem,
    RecommendationListResponse,
    RecommendationSummaryCounts,
    RejectRecommendationRequest,
)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


def generate_next_audit_id(db: Session) -> str:
    """Generates the next sequential audit_id based on MAX numeric suffix (AUD%04d)."""
    max_num = db.query(
        func.max(func.cast(func.substr(AuditLog.audit_id, 4), Integer))
    ).scalar()
    next_num = (max_num or 0) + 1
    return f"AUD{next_num:04d}"


@router.get(
    "",
    response_model=RecommendationListResponse,
    summary="List all recommendations with status/type filters and summary counts",
)
def list_recommendations(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (PENDING, APPROVED, REJECTED)"),
    recommendation_type: Optional[str] = Query(None, description="Filter by recommendation type"),
    sku_id: Optional[str] = Query(None, description="Filter by SKU ID"),
    lot_id: Optional[str] = Query(None, description="Filter by Lot ID"),
    source_location_id: Optional[str] = Query(None, description="Filter by Source Location ID"),
    target_location_id: Optional[str] = Query(None, description="Filter by Target Location ID"),
    search: Optional[str] = Query(None, description="Search by Recommendation ID or SKU Name"),
) -> RecommendationListResponse:
    # 1. Calculate overall summary counts across all 40 recommendations
    all_recs = db.query(Recommendation).all()
    pending_cnt = sum(1 for r in all_recs if r.status == "PENDING")
    approved_cnt = sum(1 for r in all_recs if r.status == "APPROVED")
    rejected_cnt = sum(1 for r in all_recs if r.status == "REJECTED")

    summary = RecommendationSummaryCounts(
        pending_count=pending_cnt,
        approved_count=approved_cnt,
        rejected_count=rejected_cnt,
        total_count=len(all_recs),
    )

    # 2. Build joined query
    query = (
        db.query(Recommendation, SKU)
        .join(SKU, Recommendation.sku_id == SKU.sku_id)
    )

    if status_filter:
        query = query.filter(Recommendation.status == status_filter.upper())
    if recommendation_type:
        query = query.filter(Recommendation.recommendation_type == recommendation_type.upper())
    if sku_id:
        query = query.filter(Recommendation.sku_id == sku_id.upper())
    if lot_id:
        query = query.filter(Recommendation.lot_id == lot_id.upper())
    if source_location_id:
        query = query.filter(Recommendation.source_location_id == source_location_id.upper())
    if target_location_id:
        query = query.filter(Recommendation.target_location_id == target_location_id.upper())

    results = query.all()

    # Pre-fetch locations map
    locations = {loc.location_id: loc.location_name for loc in db.query(Location).all()}

    items: List[RecommendationListItem] = []
    for rec, sku in results:
        if search:
            s = search.lower()
            if not (s in rec.recommendation_id.lower() or s in sku.sku_name.lower() or s in sku.sku_id.lower()):
                continue

        effective_qty = rec.adjusted_qty if rec.adjusted_qty is not None else rec.proposed_qty

        items.append(
            RecommendationListItem(
                recommendation_id=rec.recommendation_id,
                recommendation_type=rec.recommendation_type,
                sku_id=sku.sku_id,
                sku_name=sku.sku_name,
                lot_id=rec.lot_id,
                source_location_id=rec.source_location_id,
                source_location_name=locations.get(rec.source_location_id) if rec.source_location_id else None,
                target_location_id=rec.target_location_id,
                target_location_name=locations.get(rec.target_location_id) if rec.target_location_id else None,
                proposed_qty=rec.proposed_qty,
                adjusted_qty=rec.adjusted_qty,
                effective_qty=effective_qty,
                reason=rec.reason,
                status=rec.status,
                created_at=rec.created_at,
                data_status=rec.data_status,
            )
        )

    # Sort: PENDING first, created_at descending, recommendation_id
    status_order = {"PENDING": 0, "APPROVED": 1, "REJECTED": 2}
    items.sort(
        key=lambda x: (
            status_order.get(x.status, 99),
            x.created_at,
            x.recommendation_id,
        ),
        reverse=False,
    )

    return RecommendationListResponse(
        items=items,
        total=len(items),
        summary=summary,
    )


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationDetailResponse,
    summary="Get full recommendation detail with joined SKU, Lot, Locations and Audit History",
)
def get_recommendation_detail(
    recommendation_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationDetailResponse:
    rec_sku = (
        db.query(Recommendation, SKU)
        .join(SKU, Recommendation.sku_id == SKU.sku_id)
        .filter(Recommendation.recommendation_id == recommendation_id.upper())
        .first()
    )

    if not rec_sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )

    rec, sku = rec_sku
    locations = {loc.location_id: loc.location_name for loc in db.query(Location).all()}

    # Fetch lot info if present
    lot_info = None
    days_to_exp = None
    if rec.lot_id:
        lot_info = db.query(Lot).filter(Lot.lot_id == rec.lot_id).first()
        if lot_info:
            exp_date = datetime.strptime(lot_info.expiry_date, "%Y-%m-%d").date()
            days_to_exp = (exp_date - DEMO_ANALYSIS_DATE).days

    # Fetch audit history ordered chronologically
    audits = (
        db.query(AuditLog)
        .filter(AuditLog.recommendation_id == rec.recommendation_id)
        .order_by(AuditLog.action_timestamp.asc(), AuditLog.audit_id.asc())
        .all()
    )

    audit_history = [
        RecommendationAuditItem(
            audit_id=a.audit_id,
            recommendation_id=a.recommendation_id,
            actor_username=a.actor_username,
            action=a.action,
            before_status=a.before_status,
            after_status=a.after_status,
            comment=a.comment,
            action_timestamp=a.action_timestamp,
            data_status=a.data_status,
        )
        for a in audits
    ]

    effective_qty = rec.adjusted_qty if rec.adjusted_qty is not None else rec.proposed_qty

    return RecommendationDetailResponse(
        recommendation_id=rec.recommendation_id,
        recommendation_type=rec.recommendation_type,
        sku_id=sku.sku_id,
        sku_name=sku.sku_name,
        category=sku.category,
        pack_size=sku.pack_size,
        lot_id=rec.lot_id,
        expiry_date=lot_info.expiry_date if lot_info else None,
        days_to_expiry=days_to_exp,
        source_location_id=rec.source_location_id,
        source_location_name=locations.get(rec.source_location_id) if rec.source_location_id else None,
        target_location_id=rec.target_location_id,
        target_location_name=locations.get(rec.target_location_id) if rec.target_location_id else None,
        proposed_qty=rec.proposed_qty,
        adjusted_qty=rec.adjusted_qty,
        effective_qty=effective_qty,
        reason=rec.reason,
        status=rec.status,
        created_at=rec.created_at,
        data_status=rec.data_status,
        audit_history=audit_history,
    )


@router.patch(
    "/{recommendation_id}/quantity",
    response_model=RecommendationDetailResponse,
    summary="Modify recommended quantity (Warehouse Manager only)",
)
def modify_recommendation_quantity(
    recommendation_id: str,
    body: ModifyQuantityRequest,
    current_user: Annotated[User, Depends(require_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationDetailResponse:
    # 1. Validate mandatory comment
    comment_text = body.comment.strip() if body.comment else ""
    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment is mandatory for quantity modification.",
        )

    # 2. Validate positive integer
    if body.adjusted_qty <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="adjusted_qty must be a positive integer greater than zero.",
        )

    # 3. Fetch recommendation
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id.upper()).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )

    # 4. Check PENDING status -> 409 if not PENDING
    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This recommendation has already been processed.",
        )

    # 5. Atomic transaction: update adjusted_qty and insert audit_log
    try:
        rec.adjusted_qty = body.adjusted_qty
        next_audit_id = generate_next_audit_id(db)

        audit = AuditLog(
            audit_id=next_audit_id,
            recommendation_id=rec.recommendation_id,
            actor_username=current_user.username,
            action="MODIFIED",
            before_status="PENDING",
            after_status="PENDING",
            comment=comment_text,
            action_timestamp=datetime.utcnow().isoformat(),
            data_status="demo",
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record quantity modification: {str(e)}",
        )

    return get_recommendation_detail(recommendation_id, current_user, db)


@router.post(
    "/{recommendation_id}/approve",
    response_model=RecommendationDetailResponse,
    summary="Approve recommendation (Warehouse Manager only)",
)
def approve_recommendation(
    recommendation_id: str,
    body: ApproveRecommendationRequest,
    current_user: Annotated[User, Depends(require_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationDetailResponse:
    # 1. Validate mandatory comment
    comment_text = body.comment.strip() if body.comment else ""
    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment is mandatory for approval.",
        )

    # 2. Fetch recommendation
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id.upper()).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )

    # 3. Check PENDING status -> 409 if not PENDING
    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This recommendation has already been processed.",
        )

    # 4. Atomic transaction: update status to APPROVED and insert audit_log
    try:
        before_st = rec.status
        rec.status = "APPROVED"
        next_audit_id = generate_next_audit_id(db)

        audit = AuditLog(
            audit_id=next_audit_id,
            recommendation_id=rec.recommendation_id,
            actor_username=current_user.username,
            action="APPROVED",
            before_status=before_st,
            after_status="APPROVED",
            comment=comment_text,
            action_timestamp=datetime.utcnow().isoformat(),
            data_status="demo",
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record approval: {str(e)}",
        )

    return get_recommendation_detail(recommendation_id, current_user, db)


@router.post(
    "/{recommendation_id}/reject",
    response_model=RecommendationDetailResponse,
    summary="Reject recommendation (Warehouse Manager only)",
)
def reject_recommendation(
    recommendation_id: str,
    body: RejectRecommendationRequest,
    current_user: Annotated[User, Depends(require_role(APPROVER_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> RecommendationDetailResponse:
    # 1. Validate mandatory comment
    comment_text = body.comment.strip() if body.comment else ""
    if not comment_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Comment is mandatory for rejection.",
        )

    # 2. Fetch recommendation
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id.upper()).first()
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )

    # 3. Check PENDING status -> 409 if not PENDING
    if rec.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This recommendation has already been processed.",
        )

    # 4. Atomic transaction: update status to REJECTED and insert audit_log
    try:
        before_st = rec.status
        rec.status = "REJECTED"
        next_audit_id = generate_next_audit_id(db)

        audit = AuditLog(
            audit_id=next_audit_id,
            recommendation_id=rec.recommendation_id,
            actor_username=current_user.username,
            action="REJECTED",
            before_status=before_st,
            after_status="REJECTED",
            comment=comment_text,
            action_timestamp=datetime.utcnow().isoformat(),
            data_status="demo",
        )
        db.add(audit)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record rejection: {str(e)}",
        )

    return get_recommendation_detail(recommendation_id, current_user, db)
