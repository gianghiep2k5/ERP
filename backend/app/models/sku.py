"""ORM model for skus."""
from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class SKU(Base):
    __tablename__ = "skus"

    sku_id = Column(String, primary_key=True)
    public_product_id = Column(String, ForeignKey("public_products.public_product_id"), nullable=False)
    sku_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    pack_size = Column(String, nullable=True)
    variant_status = Column(String, nullable=False)
    default_shelf_life_days = Column(Integer, nullable=False)
    unit_cost_vnd = Column(Integer, nullable=False)
    source_status = Column(String, nullable=False)
