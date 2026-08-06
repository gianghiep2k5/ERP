"""ORM model for lots."""
from sqlalchemy import Column, ForeignKey, String
from app.database import Base


class Lot(Base):
    __tablename__ = "lots"

    lot_id = Column(String, primary_key=True)
    sku_id = Column(String, ForeignKey("skus.sku_id"), nullable=False)
    manufacturing_date = Column(String, nullable=False)  # ISO date string
    expiry_date = Column(String, nullable=False)          # ISO date string
    data_status = Column(String, nullable=False)
