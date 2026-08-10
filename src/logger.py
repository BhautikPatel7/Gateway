"""
src/logger.py
─────────────
Centralised logging configuration for the application.

Usage:
    from src.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from pathlib import Path


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _build_handler(stream=sys.stdout) -> logging.StreamHandler:
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    return handler


def setup_logging(level: str = "INFO") -> None:
    """
    Call once at application startup to configure the root logger.

    Args:
        level: Log level string (DEBUG | INFO | WARNING | ERROR | CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Avoid duplicate handlers if called multiple times (e.g. in tests)
    if not root.handlers:
        root.addHandler(_build_handler())

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.  Call setup_logging() once before using loggers.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        logging.Logger: Configured logger instance.
    """
    return logging.getLogger(name)
