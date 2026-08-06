"""ORM model for audit_logs."""
from sqlalchemy import Column, ForeignKey, String
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    audit_id = Column(String, primary_key=True)
    recommendation_id = Column(String, ForeignKey("recommendations.recommendation_id"), nullable=False)
    actor_username = Column(String, nullable=False)
    action = Column(String, nullable=False)         # MODIFIED, APPROVED, REJECTED
    before_status = Column(String, nullable=False)
    after_status = Column(String, nullable=False)
    comment = Column(String, nullable=True)
    action_timestamp = Column(String, nullable=False)  # ISO datetime string
    data_status = Column(String, nullable=False, default="demo")
