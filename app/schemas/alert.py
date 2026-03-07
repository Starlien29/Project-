from pydantic import BaseModel
from app.models.alert import AlertSeverity, IncidentType


class AlertCreateSchema(BaseModel):
    title: str
    body: str | None = None
    severity: AlertSeverity
    location: str | None = None
    incident_type: IncidentType = IncidentType.other
    audience: str = "all"


class AlertResponse(BaseModel):
    id: int
    title: str
    body: str | None
    severity: AlertSeverity
    location: str | None
    incident_type: IncidentType
    audience: str
    created_by_id: int | None
    created_at: datetime | None

    class Config:
        from_attributes = True
