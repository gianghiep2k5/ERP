"""Pydantic schemas for Expiry Risk endpoints."""
from typing import List, Optional
from pydantic import BaseModel


class ExpiryRiskItem(BaseModel):
    inventory_id: str
    lot_id: str
    sku_id: str
    sku_name: str
    category: str
    location_id: str
    location_name: str
    available_qty: int
    on_hand_qty: int
    manufacturing_date: str
    expiry_date: str
    analysis_date: str
    days_to_expiry: int
    recent_30d_sales_qty: int
    recent_average_daily_demand: float
    forecast_consumption_before_expiry: float
    forecast_method: str
    projected_surplus: float
    projected_shortage: float
    surplus_ratio: float
    urgency_factor: float
    risk_score: float
    risk_band: str
    explanation: str
    proposed_actions: List[str]
    fefo_position: int
    related_recommendation_ids: List[str]
    pack_size: Optional[str] = None
    public_product_id: Optional[str] = None
    product_name: Optional[str] = None
    source_url: Optional[str] = None


class ExpiryRiskSummaryCounts(BaseModel):
    expired_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    total_projected_surplus: float


class ExpiryRiskListResponse(BaseModel):
    items: List[ExpiryRiskItem]
    total: int
    summary: ExpiryRiskSummaryCounts
