"""
main.py
───────
Application entry point.

Run directly:
    python main.py

Or via uvicorn (recommended for development):
    uvicorn src.app:app --reload --host 0.0.0.0 --port 8002
"""

import uvicorn
from src.config import settings  # triggers fail-fast validation on startup


def main() -> None:
    uvicorn.run(
        "src.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
