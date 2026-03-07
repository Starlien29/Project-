"""IncidentReport model - user-reported concerns (FR-12)."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.alert import AlertSeverity


class ReportStatus(str, enum.Enum):
    pending = "pending"
    acknowledged = "acknowledged"
    resolved = "resolved"


class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id = Column(Integer, primary_key=True, index=True)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=True)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.Medium)
    status = Column(Enum(ReportStatus), nullable=False, default=ReportStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow)

    reported_by_user = relationship("User", back_populates="incident_reports")
