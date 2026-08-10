"""
src/services/health_service.py
──────────────────────────────
Business logic for the health-check endpoint.
All heavier logic should live in service files like this one — keep routes thin.
"""

from src.config import settings
from src.logger import get_logger

logger = get_logger(__name__)


def get_health_status() -> dict:
    """
    Return a dictionary describing the current health of the application.

    Returns:
        dict: Status payload.
    """
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "debug": settings.DEBUG,
    }
