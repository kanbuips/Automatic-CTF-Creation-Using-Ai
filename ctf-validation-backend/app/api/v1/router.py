"""Aggregates all v1 routes."""
from fastapi import APIRouter, Depends

from app.api.deps import require_api_key
from app.api.v1 import approval, compare, generate, health, reports, upload, validation

api_router = APIRouter()
api_router.include_router(health.router)

protected = APIRouter(dependencies=[Depends(require_api_key)])
protected.include_router(upload.router, prefix="/upload")
protected.include_router(validation.router, prefix="/validate")
protected.include_router(reports.router, prefix="/reports")
protected.include_router(approval.router, prefix="/approval")
protected.include_router(generate.router, prefix="/generate")
protected.include_router(compare.router, prefix="/compare")
api_router.include_router(protected)
