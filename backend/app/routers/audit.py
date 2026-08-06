"""Audit Log router: GET /api/audit and GET /api/audit/{audit_id}."""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import READ_ALL_ROLES, require_role
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditListItem, AuditListResponse

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get(
    "",
    response_model=AuditListResponse,
    summary="List audit log entries with filters and sorting (action_timestamp desc)",
)
def list_audit_logs(
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
    recommendation_id: Optional[str] = Query(None, description="Filter by Recommendation ID"),
    actor_username: Optional[str] = Query(None, description="Filter by Actor Username"),
    action: Optional[str] = Query(None, description="Filter by Action (MODIFIED, APPROVED, REJECTED)"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
) -> AuditListResponse:
    """Returns audit log history ordered by action_timestamp descending and audit_id descending."""
    query = db.query(AuditLog)

    if recommendation_id:
        query = query.filter(AuditLog.recommendation_id == recommendation_id.upper())
    if actor_username:
        query = query.filter(AuditLog.actor_username == actor_username)
    if action:
        query = query.filter(AuditLog.action == action.upper())
    if start_date:
        query = query.filter(AuditLog.action_timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.action_timestamp <= end_date + "T23:59:59")

    query = query.order_by(AuditLog.action_timestamp.desc(), AuditLog.audit_id.desc())

    audits = query.all()

    items = [
        AuditListItem(
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

    return AuditListResponse(
        items=items,
        total=len(items),
    )


@router.get(
    "/{audit_id}",
    response_model=AuditListItem,
    summary="Get single audit log entry detail",
)
def get_audit_log_detail(
    audit_id: str,
    current_user: Annotated[User, Depends(require_role(READ_ALL_ROLES))],
    db: Annotated[Session, Depends(get_db)],
) -> AuditListItem:
    audit = db.query(AuditLog).filter(AuditLog.audit_id == audit_id.upper()).first()
    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log entry '{audit_id}' not found",
        )

    return AuditListItem(
        audit_id=audit.audit_id,
        recommendation_id=audit.recommendation_id,
        actor_username=audit.actor_username,
        action=audit.action,
        before_status=audit.before_status,
        after_status=audit.after_status,
        comment=audit.comment,
        action_timestamp=audit.action_timestamp,
        data_status=audit.data_status,
    )
