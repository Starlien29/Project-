"""Alert model - severity, location, incident type (FR-08, FR-09, FR-14)."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class AlertSeverity(str, enum.Enum):
    Critical = "critical"
    High = "high"
    Medium = "medium"
    Low = "low"


class IncidentType(str, enum.Enum):
    fire = "fire"
    medical = "medical"
    security_threat = "security_threat"
    weather = "weather"
    other = "other"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False)
    location = Column(String(255), nullable=True)  # campus zone/building
    incident_type = Column(Enum(IncidentType), nullable=False, default=IncidentType.other)
    audience = Column(String(64), nullable=False, default="all")  # all | role:student | etc.
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 90-day retention (FR-14)

    created_by_user = relationship("User", back_populates="alerts_created", foreign_keys=[created_by_id])

    __table_args__ = (Index("ix_alerts_created_at", "created_at"),)
