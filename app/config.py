from pydantic_settings import BaseSettings
from pydantic import EmailStr, AnyUrl, SecretStr
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Core settings
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "your-secret-key-change-this-in-production"
    access_token_expire_minutes: int = 30
    environment: str = "development"  # "development" or "production"

    # Email settings
    resend_api_key: Optional[SecretStr] = None
    email_from: EmailStr = "noreply@example.com"
    email_from_name: str = "FastAPI App"
    reset_url_base: AnyUrl = "http://localhost:8000/reset"

    # Optional webhook secret
    resend_webhook_secret: Optional[SecretStr] = None

    # Logging settings
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir: str = "logs"
    log_file: str = "app.log"
    log_max_bytes: int = 5 * 1024 * 1024  # 5MB
    log_backup_count: int = 5
    log_to_console: bool = True

    @property
    def cookie_secure(self) -> bool:
        """Return True if cookies should use secure flag (HTTPS only)"""
        return self.environment == "production"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env file


@lru_cache()
def get_settings():
    return Settings()