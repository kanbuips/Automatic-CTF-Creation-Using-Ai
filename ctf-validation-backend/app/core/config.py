"""Settings (pydantic-settings, .env)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CTF Validation API"
    log_level: str = "INFO"
    database_url: str = f"sqlite:///{BASE_DIR / 'ctf.db'}"
    api_key: str = ""  # empty disables auth
    cors_origins: list[str] = ["http://localhost:5173"]

    upload_dir: Path = BASE_DIR / "storage" / "uploads"
    report_dir: Path = BASE_DIR / "storage" / "reports"
    artifact_dir: Path = BASE_DIR / "ml" / "artifacts"
    max_upload_mb: int = 20

    required_template: str = "Beta 3"
    rejected_templates: list[str] = ["Beta 2"]
    classifier_threshold: float = 0.7
    anomaly_min_batch: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
