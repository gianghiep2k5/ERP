"""ORM model for locations."""
from sqlalchemy import Column, String
from app.database import Base


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(String, primary_key=True)
    location_name = Column(String, nullable=False)
    location_type = Column(String, nullable=False)
    data_status = Column(String, nullable=False)
