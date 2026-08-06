"""ORM model for forecast_metrics."""
from sqlalchemy import Column, Float, ForeignKey, Integer, String
from app.database import Base


class ForecastMetric(Base):
    __tablename__ = "forecast_metrics"

    forecast_run_id = Column(String, primary_key=True)
    sku_id = Column(String, ForeignKey("skus.sku_id"), nullable=False)
    model_name = Column(String, nullable=False)
    evaluation_window_days = Column(Integer, nullable=False)
    wape = Column(Float, nullable=False)
    bias = Column(Float, nullable=False)
    run_date = Column(String, nullable=False)
    data_status = Column(String, nullable=False)
