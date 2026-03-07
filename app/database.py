"""SQLAlchemy engine, session, and base for SQLite."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool
from app.config import get_settings

settings = get_settings()

# Use StaticPool for SQLite to work well with async/threading if needed
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    poolclass=StaticPool if "sqlite" in settings.database_url else None,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Call on startup or via CLI."""
    from app.models import user, session, alert, incident_report, audit_log, login_attempt  # noqa: F401
    Base.metadata.create_all(bind=engine)
