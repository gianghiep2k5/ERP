"""ORM model for inventory_balances."""
from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class InventoryBalance(Base):
    __tablename__ = "inventory_balances"

    inventory_id = Column(String, primary_key=True)
    lot_id = Column(String, ForeignKey("lots.lot_id"), nullable=False)
    location_id = Column(String, ForeignKey("locations.location_id"), nullable=False)
    on_hand_qty = Column(Integer, nullable=False)
    available_qty = Column(Integer, nullable=False)
    reserved_qty = Column(Integer, nullable=False)
    quarantine_qty = Column(Integer, nullable=False)
    last_updated = Column(String, nullable=False)  # ISO datetime string
    scenario = Column(String, nullable=False)       # normal/stockout/expiry/transfer
    data_status = Column(String, nullable=False)
