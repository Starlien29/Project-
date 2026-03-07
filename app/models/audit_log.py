"""AuditLog model - append-only for admin and system actions (FR-22, FR-23)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    details = Column(Text, nullable=True)  # JSON or text
    ip_address = Column(String(45), nullable=True)

    actor = relationship("User", back_populates="audit_logs", foreign_keys=[actor_id])
