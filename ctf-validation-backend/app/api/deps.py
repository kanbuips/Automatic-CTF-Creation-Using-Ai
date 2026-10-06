"""Shared dependencies (DB session, API-key auth)."""
from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthError
from app.core.security import verify_api_key
from app.db.session import get_db

__all__ = ["get_db", "require_api_key"]


def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not verify_api_key(x_api_key, settings.api_key):
        raise AuthError("Invalid or missing API key")
