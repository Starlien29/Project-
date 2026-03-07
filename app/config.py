"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """CSAS settings loaded from env."""

    # Database
    database_url: str = "sqlite:///./csas.db"

    # Security
    secret_key: str = "change-me-in-production-use-env-var"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    bcrypt_rounds: int = 12

    # Session (FR-05: configurable inactivity, default 30 min)
    session_expire_minutes: int = 30

    # Rate limiting (FR-21)
    rate_limit_login: str = "5/minute"
    rate_limit_alerts: str = "30/minute"

    # App
    app_name: str = "Campus Security Alert System"
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
