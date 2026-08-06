"""ORM model for forecast_reviews."""
from sqlalchemy import Column, ForeignKey, String
from app.database import Base


class ForecastReview(Base):
    __tablename__ = "forecast_reviews"

    review_id = Column(String, primary_key=True)
    forecast_run_id = Column(String, ForeignKey("forecast_metrics.forecast_run_id"), nullable=False)
    reviewer_username = Column(String, nullable=False)
    review_status = Column(String, nullable=False)  # ACCEPTED_AS_BASELINE, ADJUSTMENT_REQUIRED, MONITOR
    planner_comment = Column(String, nullable=False)
    reviewed_at = Column(String, nullable=False)    # ISO datetime string
