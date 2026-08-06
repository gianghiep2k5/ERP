"""Pydantic schemas for GET /api/dashboard/summary."""
from typing import Optional
from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_skus: int
    total_lots: int
    total_on_hand_qty: int
    pending_recommendations: int
    stockout_count: int
    expiry_count: int
    transfer_count: int
    normal_count: int
    latest_update: Optional[str]   # ISO datetime of MAX(last_updated)
    analysis_date: str             # DEMO_ANALYSIS_DATE as "YYYY-MM-DD"
