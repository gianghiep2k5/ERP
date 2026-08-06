"""Pydantic schemas for Demand Forecast and Planner Review endpoints."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ForecastSKUListItem(BaseModel):
    sku_id: str
    sku_name: str
    category: str
    forecast_run_id: str
    wape: float
    bias: float
    model_name: str
    review_status: Optional[str] = None


class SalesObservation(BaseModel):
    sales_date: str
    quantity_sold: int


class ForecastObservation(BaseModel):
    forecast_date: str
    forecast_qty: int


class ReviewItem(BaseModel):
    review_id: str
    forecast_run_id: str
    reviewer_username: str
    review_status: str
    planner_comment: str
    reviewed_at: str


class ForecastSKUDetailResponse(BaseModel):
    sku_id: str
    sku_name: str
    category: str
    analysis_date: str
    actual_start_date: str
    actual_end_date: str
    actual_sales: List[SalesObservation]
    forecast_start_date: str
    forecast_end_date: str
    forecast_results: List[ForecastObservation]
    forecast_run_id: str
    model_name: str
    wape: float
    bias: float
    evaluation_window_days: int
    latest_review: Optional[ReviewItem] = None
    review_history: List[ReviewItem] = Field(default_factory=list)


class CreateReviewRequest(BaseModel):
    review_status: str
    planner_comment: str
