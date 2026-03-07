"""Incident reporting API (FR-12)."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.user import User, UserRole
from app.models.incident_report import IncidentReport, ReportStatus
from app.schemas.incident import IncidentReportCreate, IncidentReportResponse
from app.services.audit import log_audit
from app.services.realtime import sse_manager

router = APIRouter()


def _report_to_dict(r: IncidentReport) -> dict:
    return {
        "type": "incident_report",
        "id": r.id,
        "description": r.description,
        "location": r.location,
        "severity": r.severity.value,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.post("", response_model=IncidentReportResponse)
def report_incident(
    data: IncidentReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Report an incident; notifies security (FR-12)."""
    report = IncidentReport(
        reported_by_id=current_user.id,
        description=data.description,
        location=data.location,
        severity=data.severity,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    log_audit(
        db,
        action="incident_report",
        actor_id=current_user.id,
        resource_type="incident_report",
        resource_id=str(report.id),
        details=data.model_dump_json(),
        ip_address=request.client.host if request.client else None,
    )
    sse_manager.broadcast_alert_sync(_report_to_dict(report))
    return IncidentReportResponse(
        id=report.id,
        reported_by_id=report.reported_by_id,
        description=report.description,
        location=report.location,
        severity=report.severity,
        status=report.status,
        created_at=report.created_at,
    )


@router.get("", response_model=list[IncidentReportResponse])
def list_incidents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List incident reports. Security/Admin see all; others see own."""
    if current_user.role in (UserRole.SecurityOfficer, UserRole.Administrator):
        reports = db.query(IncidentReport).order_by(IncidentReport.created_at.desc()).all()
    else:
        reports = db.query(IncidentReport).filter(IncidentReport.reported_by_id == current_user.id).order_by(IncidentReport.created_at.desc()).all()
    return [
        IncidentReportResponse(
            id=r.id,
            reported_by_id=r.reported_by_id,
            description=r.description,
            location=r.location,
            severity=r.severity,
            status=r.status,
            created_at=r.created_at,
        )
        for r in reports
    ]
