"""User model - university credentials, role, optional 2FA (FR-01, FR-03, FR-06)."""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    Student = "student"
    Staff = "staff"
    SecurityOfficer = "security_officer"
    Administrator = "administrator"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    university_id = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.Student)
    two_fa_secret = Column(String(32), nullable=True)  # TOTP secret (FR-06)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    alerts_created = relationship("Alert", back_populates="created_by_user", foreign_keys="Alert.created_by_id")
    incident_reports = relationship("IncidentReport", back_populates="reported_by_user")
    audit_logs = relationship("AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id")
