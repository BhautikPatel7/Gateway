"""
src/app.py
──────────
FastAPI application factory.

All router registration, middleware, and lifespan hooks live here.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.config import settings
from src.logger import get_logger, setup_logging
from src.routes.health_router import router as health_router
from src.routes.triage_router import router as triage_router

# Absolute path to the static/ folder at the project root
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Code before `yield`  → runs on startup.
    Code after  `yield`  → runs on shutdown.
    """
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"  Starting {settings.APP_NAME}")
    logger.info(f"  Env    : {settings.APP_ENV}")
    logger.info(f"  Debug  : {settings.DEBUG}")
    logger.info(f"  Port   : {settings.PORT}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    yield
    logger.info(f"  {settings.APP_NAME} shut down cleanly.")


def create_app() -> FastAPI:
    """
    Construct and configure the FastAPI application.

    Returns:
        FastAPI: Fully configured application instance.
    """
    # ── Bootstrap logging first so every subsequent log is captured ──────────
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    setup_logging(level=log_level)

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="FRONTLINE — AI Customer Message Triage System API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── Register routers ────────────────────────────────────────────────────────
    app.include_router(health_router, prefix="/api")
    app.include_router(triage_router)   # prefix already set in router (/api/triage)

    # ── Serve the frontend ───────────────────────────────────────────────────
    # GET /  → index.html (the triage UI)
    @app.get("/", include_in_schema=False)
    async def serve_ui() -> FileResponse:
        return FileResponse(_STATIC_DIR / "index.html")

    # Mount remaining static assets (CSS/JS/images if added later)
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    return app


# Module-level singleton used by uvicorn
app: FastAPI = create_app()
