"""Audit logging (FR-22, FR-23)."""
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    action: str,
    actor_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Append-only audit log entry."""
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
    )
    db.commit()
