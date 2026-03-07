"""LoginAttempt model - failed/success login logging (FR-07)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.database import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    identifier = Column(String(255), nullable=False)  # email or university_id
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
