"""Settings (pydantic-settings, .env)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CTF Validation API"
    database_url: str = "sqlite:///./ctf.db"
    secret_key: str = "change-me"
    cors_origins: list[str] = ["http://localhost:5173"]
    upload_dir: str = "storage/uploads"
    report_dir: str = "storage/reports"


@lru_cache
def get_settings() -> Settings:
    return Settings()
