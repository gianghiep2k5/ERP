"""ORM model for sales_history."""
from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sales_date = Column(String, nullable=False)  # ISO date YYYY-MM-DD
    sku_id = Column(String, ForeignKey("skus.sku_id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.location_id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    promotion_flag = Column(Integer, nullable=False, default=0)
    data_status = Column(String, nullable=False)
