"""Aggregates all v1 routes."""
from fastapi import APIRouter

from app.api.v1 import approval, health, reports, upload, validation

api_router = APIRouter()
api_router.include_router(health.router)
# api_router.include_router(upload.router, prefix="/upload")
# api_router.include_router(validation.router, prefix="/validate")
# api_router.include_router(reports.router, prefix="/reports")
# api_router.include_router(approval.router, prefix="/approval")
