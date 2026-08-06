"""ORM model for public_products."""
from sqlalchemy import Column, String
from app.database import Base


class PublicProduct(Base):
    __tablename__ = "public_products"

    public_product_id = Column(String, primary_key=True)
    product_name = Column(String, nullable=False)
    public_pack_size = Column(String, nullable=True)
    category = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
