from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    environment: str = "development"  # "development" or "production"

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