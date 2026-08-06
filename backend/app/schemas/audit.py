"""Pydantic schemas for Audit Log endpoints."""
from typing import List, Optional
from pydantic import BaseModel


class AuditListItem(BaseModel):
    audit_id: str
    recommendation_id: str
    actor_username: str
    action: str
    before_status: str
    after_status: str
    comment: Optional[str] = None
    action_timestamp: str
    data_status: str


class AuditListResponse(BaseModel):
    items: List[AuditListItem]
    total: int
