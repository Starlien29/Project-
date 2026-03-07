"""Admin API: user/role management (FR-04), audit log (FR-23)."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas.user import UserResponse, UserRoleUpdate
from app.services.audit import log_audit

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator])),
):
    """List all users (admin only)."""
    users = db.query(User).order_by(User.id).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            university_id=u.university_id,
            role=u.role,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator])),
):
    """Assign/modify/revoke user role (FR-04). Logged to audit (FR-23)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_role = user.role.value
    user.role = data.role
    db.commit()
    db.refresh(user)
    log_audit(
        db,
        action="role_change",
        actor_id=current_user.id,
        resource_type="user",
        resource_id=str(user_id),
        details=f"role:{old_role}->{data.role.value}",
        ip_address=request.client.host if request.client else None,
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        university_id=user.university_id,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/audit", response_model=list[dict])
def list_audit_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.Administrator, UserRole.SecurityOfficer])),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(500, le=2000),
):
    """Filter and export audit log (FR-25)."""
    q = db.query(AuditLog).order_by(AuditLog.timestamp.desc())
    if date_from:
        from datetime import datetime
        try:
            q = q.filter(AuditLog.timestamp >= datetime.fromisoformat(date_from.replace("Z", "+00:00")))
        except ValueError:
            pass
    if date_to:
        from datetime import datetime
        try:
            q = q.filter(AuditLog.timestamp <= datetime.fromisoformat(date_to.replace("Z", "+00:00")))
        except ValueError:
            pass
    if action:
        q = q.filter(AuditLog.action == action)
    rows = q.limit(limit).all()
    return [
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
