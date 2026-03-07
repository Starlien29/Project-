"""Dashboard API: metrics, export, heat-map data (FR-24, FR-25, FR-26, FR-27)."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.models.alert import Alert, AlertSeverity
from app.models.incident_report import IncidentReport
from app.models.audit_log import AuditLog

router = APIRouter()


@router.get("/metrics")
def get_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator, UserRole.SecurityOfficer])),
    days: int = Query(30, ge=1, le=90),
):
    """Real-time and historical metrics (FR-24): alert frequency, high-risk zones, incident types."""
    since = datetime.utcnow() - timedelta(days=days)
    alerts = db.query(Alert).filter(Alert.created_at >= since).all()
    incidents = db.query(IncidentReport).filter(IncidentReport.created_at >= since).all()

    alert_by_severity = {}
    for s in AlertSeverity:
        alert_by_severity[s.value] = sum(1 for a in alerts if a.severity == s)
    location_counts = {}
    for a in alerts:
        loc = a.location or "Unknown"
        location_counts[loc] = location_counts.get(loc, 0) + 1
    incident_type_counts = {}
    for i in incidents:
        t = i.severity.value
        incident_type_counts[t] = incident_type_counts.get(t, 0) + 1

    return {
        "period_days": days,
        "alerts_total": len(alerts),
        "alerts_by_severity": alert_by_severity,
        "incidents_total": len(incidents),
        "high_risk_locations": dict(sorted(location_counts.items(), key=lambda x: -x[1])[:10]),
        "incident_types": incident_type_counts,
    }


@router.get("/audit/export")
def export_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator, UserRole.SecurityOfficer])),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    format: str = Query("csv", regex="^(csv|json)$"),
):
    """Export audit log by date range (FR-25)."""
    q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if date_from:
        try:
            q = q.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from.replace("Z", "+00:00")))
        except ValueError:
            pass
    if date_to:
        try:
            q = q.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to.replace("Z", "+00:00")))
        except ValueError:
            pass
    rows = q.limit(10000).all()
    if format == "json":
        import json
        data = [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "actor_id": r.actor_id,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "details": r.details,
                "ip_address": r.ip_address,
            }
            for r in rows
        ]
        return StreamingResponse(
            iter([json.dumps(data)]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=audit_export.json"},
        )
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["id", "timestamp", "actor_id", "action", "resource_type", "resource_id", "details", "ip_address"])
    for r in rows:
        w.writerow([r.id, r.timestamp, r.actor_id, r.action, r.resource_type, r.resource_id, r.details, r.ip_address])
    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_export.csv"},
    )


@router.get("/report")
def automated_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator])),
    period: str = Query("day", regex="^(day|week|month)$"),
):
    """Automated summary report for admins (FR-26). Call via cron for daily/weekly/monthly."""
    from datetime import timedelta
    if period == "day":
        since = datetime.utcnow() - timedelta(days=1)
    elif period == "week":
        since = datetime.utcnow() - timedelta(days=7)
    else:
        since = datetime.utcnow() - timedelta(days=30)
    alerts = db.query(Alert).filter(Alert.created_at >= since).all()
    incidents = db.query(IncidentReport).filter(IncidentReport.created_at >= since).all()
    return {
        "period": period,
        "from": since.isoformat(),
        "alerts_count": len(alerts),
        "incidents_count": len(incidents),
        "summary": "Campus security activity report.",
    }


@router.get("/heatmap")
def heatmap_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator, UserRole.SecurityOfficer])),
    days: int = Query(30, ge=1, le=90),
):
    """Heat-map / geographic data: counts by location (FR-27)."""
    since = datetime.utcnow() - timedelta(days=days)
    alerts = db.query(Alert.location, func.count(Alert.id)).filter(
        Alert.created_at >= since,
        Alert.location.isnot(None),
    ).group_by(Alert.location).all()
    incidents = db.query(IncidentReport.location, func.count(IncidentReport.id)).filter(
        IncidentReport.created_at >= since,
        IncidentReport.location.isnot(None),
    ).group_by(IncidentReport.location).all()
    by_location = {}
    for loc, c in alerts:
        by_location[loc] = by_location.get(loc, 0) + c
    for loc, c in incidents:
        by_location[loc] = by_location.get(loc, 0) + c
    return {"locations": [{"name": k, "count": v} for k, v in sorted(by_location.items(), key=lambda x: -x[1])]}
