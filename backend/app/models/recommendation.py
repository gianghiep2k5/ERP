"""ORM model for recommendations."""
from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(String, primary_key=True)
    recommendation_type = Column(String, nullable=False)
    sku_id = Column(String, ForeignKey("skus.sku_id"), nullable=False)
    lot_id = Column(String, ForeignKey("lots.lot_id"), nullable=True)
    source_location_id = Column(String, ForeignKey("locations.location_id"), nullable=True)
    target_location_id = Column(String, ForeignKey("locations.location_id"), nullable=True)
    proposed_qty = Column(Integer, nullable=False)
    adjusted_qty = Column(Integer, nullable=True)   # NULL until manager modifies
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False)         # PENDING/APPROVED/REJECTED
    created_at = Column(String, nullable=False)
    data_status = Column(String, nullable=False)
