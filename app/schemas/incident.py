from datetime import datetime
from pydantic import BaseModel
from app.models.alert import AlertSeverity
from app.models.incident_report import ReportStatus


class IncidentReportCreate(BaseModel):
    description: str
    location: str | None = None
    severity: AlertSeverity = AlertSeverity.Medium


class IncidentReportResponse(BaseModel):
    id: int
    reported_by_id: int
    description: str
    location: str | None
    severity: AlertSeverity
    status: ReportStatus
    created_at: datetime | None

    class Config:
        from_attributes = True
