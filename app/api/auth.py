"""Auth API: register, login, logout (FR-01, FR-05, FR-07)."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    log_login_attempt,
    get_current_user,
)
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.session import Session as SessionModel
from app.schemas.user import UserCreate, UserResponse
from app.middleware import limiter

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """Register with university ID and institutional email (FR-01)."""
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.university_id == data.university_id).first():
        raise HTTPException(status_code=400, detail="University ID already registered")
    user = User(
        email=data.email,
        university_id=data.university_id,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        email=user.email,
        university_id=user.university_id,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Login with email or university_id as username (FR-01). Returns JWT."""
    ip_address = request.client.host if request.client else None
    identifier = form.username
    password = form.password
    user = db.query(User).filter(
        (User.email == identifier) | (User.university_id == identifier)
    ).first()
    if not user or not verify_password(password, user.password_hash):
        log_login_attempt(db, identifier, False, ip_address)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    log_login_attempt(db, identifier, True, ip_address)
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    expires = datetime.utcnow() + timedelta(minutes=settings.session_expire_minutes)
    session = SessionModel(
        user_id=user.id,
        token=token,
        expires_at=expires,
    )
    db.add(session)
    db.commit()
    return {"access_token": token, "token_type": "bearer", "expires_in": settings.session_expire_minutes * 60}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Current user info."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        university_id=current_user.university_id,
        role=current_user.role,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )
