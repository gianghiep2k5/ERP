"""ORM model for forecast_results."""
from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    forecast_run_id = Column(String, nullable=False)
    sku_id = Column(String, ForeignKey("skus.sku_id"), nullable=False)
    forecast_date = Column(String, nullable=False)  # ISO date YYYY-MM-DD
    forecast_qty = Column(Integer, nullable=False)
    model_name = Column(String, nullable=False)
    data_status = Column(String, nullable=False)
