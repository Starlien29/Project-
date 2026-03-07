"""Alerts API: create/broadcast (Security Officer/Admin), list (FR-08–FR-14)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user_optional, require_roles, get_current_user
from app.database import get_db
from app.models.user import User, UserRole
from app.models.alert import Alert, AlertSeverity, IncidentType
from app.schemas.alert import AlertCreateSchema, AlertResponse
from app.services.audit import log_audit
from app.services.realtime import sse_manager, event_generator
from app.middleware import limiter

router = APIRouter()

# 90 days retention (FR-14)
ALERT_RETENTION_DAYS = 90


def _alert_to_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "title": alert.title,
        "body": alert.body,
        "severity": alert.severity.value,
        "location": alert.location,
        "incident_type": alert.incident_type.value,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
    }


@router.post("", response_model=AlertResponse)
@limiter.limit("30/minute")
def create_alert(
    data: AlertCreateSchema,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SecurityOfficer, UserRole.Administrator])),
):
    """Create and broadcast alert (FR-08, FR-09)."""
    expires_at = datetime.utcnow() + timedelta(days=ALERT_RETENTION_DAYS)
    alert = Alert(
        title=data.title,
        body=data.body,
        severity=data.severity,
        location=data.location,
        incident_type=data.incident_type,
        audience=data.audience,
        created_by_id=current_user.id,
        expires_at=expires_at,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    log_audit(
        db,
        action="alert_broadcast",
        actor_id=current_user.id,
        resource_type="alert",
        resource_id=str(alert.id),
        details=data.model_dump_json(),
        ip_address=request.client.host if request.client else None,
    )
    # Real-time push (FR-10)
    sse_manager.broadcast_alert_sync(_alert_to_dict(alert))
    return AlertResponse(
        id=alert.id,
        title=alert.title,
        body=alert.body,
        severity=alert.severity,
        location=alert.location,
        incident_type=alert.incident_type,
        audience=alert.audience,
        created_by_id=alert.created_by_id,
        created_at=alert.created_at,
    )


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    limit: int = 100,
):
    """List recent alerts (90-day window, FR-14). Sorted by severity then time (FR-13)."""
    cutoff = datetime.utcnow() - timedelta(days=ALERT_RETENTION_DAYS)
    q = db.query(Alert).filter(Alert.created_at >= cutoff).order_by(
        Alert.severity.asc(),
        Alert.created_at.desc(),
    )
    alerts = q.limit(limit).all()
    severity_order = {AlertSeverity.Critical: 0, AlertSeverity.High: 1, AlertSeverity.Medium: 2, AlertSeverity.Low: 3}
    alerts = sorted(alerts, key=lambda a: (severity_order.get(a.severity, 4), -(a.created_at or datetime.min).timestamp()))
    return [
        AlertResponse(
            id=a.id,
            title=a.title,
            body=a.body,
            severity=a.severity,
            location=a.location,
            incident_type=a.incident_type,
            audience=a.audience,
            created_by_id=a.created_by_id,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.get("/stream")
async def stream_alerts(
    current_user: User | None = Depends(get_current_user_optional),
):
    """SSE endpoint for real-time alerts (FR-10)."""
    queue = sse_manager.subscribe()
    try:
        return StreamingResponse(
            event_generator(queue),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    finally:
        sse_manager.unsubscribe(queue)
