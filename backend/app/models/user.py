"""SQLAlchemy ORM model for the users table."""
from sqlalchemy import Column, String
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    # password_hash is stored but NEVER returned by any API response.
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
