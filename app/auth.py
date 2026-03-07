"""Authentication: bcrypt, JWT, RBAC, session expiry (FR-05, FR-15, FR-20)."""
import secrets
from datetime import datetime, timedelta
from typing import Annotated

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole
from app.models.session import Session as SessionModel
from app.models.login_attempt import LoginAttempt

settings = get_settings()
security = HTTPBearer(auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """Hash with bcrypt cost 12 (FR-15)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rounds)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def create_session_token() -> str:
    return secrets.token_urlsafe(32)


def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
    db: Session = Depends(get_db),
) -> User | None:
    """Return current user if valid Bearer token, else None."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return None
    user = db.query(User).filter(User.id == uid).first()
    return user


def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    """Require authenticated user (FR-20)."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(allowed_roles: list[UserRole]):
    """Dependency: require current user to have one of the given roles (FR-03)."""

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def log_login_attempt(db: Session, identifier: str, success: bool, ip_address: str | None) -> None:
    """FR-07: log every login attempt."""
    db.add(LoginAttempt(identifier=identifier, success=success, ip_address=ip_address))
    db.commit()
