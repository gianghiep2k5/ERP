"""Pydantic schemas for Recommendation endpoints."""
from typing import List, Optional
from pydantic import BaseModel


class RecommendationListItem(BaseModel):
    recommendation_id: str
    recommendation_type: str
    sku_id: str
    sku_name: str
    lot_id: Optional[str] = None
    source_location_id: Optional[str] = None
    source_location_name: Optional[str] = None
    target_location_id: Optional[str] = None
    target_location_name: Optional[str] = None
    proposed_qty: int
    adjusted_qty: Optional[int] = None
    effective_qty: int
    reason: str
    status: str
    created_at: str
    data_status: str


class RecommendationSummaryCounts(BaseModel):
    pending_count: int
    approved_count: int
    rejected_count: int
    total_count: int


class RecommendationListResponse(BaseModel):
    items: List[RecommendationListItem]
    total: int
    summary: RecommendationSummaryCounts


class RecommendationAuditItem(BaseModel):
    audit_id: str
    recommendation_id: str
    actor_username: str
    action: str
    before_status: str
    after_status: str
    comment: Optional[str] = None
    action_timestamp: str
    data_status: str


class RecommendationDetailResponse(BaseModel):
    recommendation_id: str
    recommendation_type: str
    sku_id: str
    sku_name: str
    category: str
    pack_size: Optional[str] = None
    lot_id: Optional[str] = None
    expiry_date: Optional[str] = None
    days_to_expiry: Optional[int] = None
    source_location_id: Optional[str] = None
    source_location_name: Optional[str] = None
    target_location_id: Optional[str] = None
    target_location_name: Optional[str] = None
    proposed_qty: int
    adjusted_qty: Optional[int] = None
    effective_qty: int
    reason: str
    status: str
    created_at: str
    data_status: str
    audit_history: List[RecommendationAuditItem]


class ModifyQuantityRequest(BaseModel):
    adjusted_qty: int
    comment: str


class ApproveRecommendationRequest(BaseModel):
    comment: str


class RejectRecommendationRequest(BaseModel):
    comment: str
