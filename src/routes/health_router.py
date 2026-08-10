"""
src/routes/health_router.py
────────────────────────────
Health-check route.  Delegates all logic to health_service.
Add new routers in this folder and include them in src/app.py.
"""

from fastapi import APIRouter
from src.services.health_service import get_health_status

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Health check")
async def health_check() -> dict:
    """
    Returns the current health status of the API.
    """
    return get_health_status()
