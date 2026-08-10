"""
src/config.py
─────────────
Application configuration loaded from environment variables via a .env file.

All required fields are declared with no default value — pydantic-settings will
raise a ValidationError (and the app will refuse to start) if any of them are
missing from the environment.

Usage:
    from src.config import settings
    print(settings.APP_NAME)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from pathlib import Path


# Locate the .env file relative to this file (project root)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """
    Application settings.

    Required fields (no defaults) will cause the app to FAIL FAST on startup
    if they are absent from the .env file or the environment.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # silently ignore unknown env vars
    )

    # ── Required ─────────────────────────────────────────────────────────────
    APP_NAME: str = Field(..., description="Human-readable application name")
    APP_ENV: str = Field(..., description="Runtime environment: development | staging | production")
    SECRET_KEY: str = Field(..., description="Secret key used for signing / encryption")

    # ── Optional with sensible defaults ──────────────────────────────────────
    HOST: str = Field(default="0.0.0.0", description="Bind address for the HTTP server")
    PORT: int = Field(default=8002, description="TCP port for the HTTP server")
    DEBUG: bool = Field(default=False, description="Enable debug mode")

    # ── Groq LLM ─────────────────────────────────────────────────────────────
    GROQ_API_KEY: str = Field(..., description="Groq API key")
    GROQ_MODEL: str = Field(default="llama-3.1-8b-instant", description="Groq model to use")

    # ── Triage settings ───────────────────────────────────────────────────────
    CONFIDENCE_THRESHOLD: float = Field(default=0.80, description="Below this score, needs_human is forced true")

    # ── Derived / computed ────────────────────────────────────────────────────
    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v.lower() not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("SECRET_KEY must not be empty")
        return v


def _load_settings() -> Settings:
    """
    Load and validate settings.  Raises a descriptive error and exits if any
    required environment variable is missing or invalid.
    """
    import sys
    from pydantic import ValidationError

    try:
        return Settings()
    except ValidationError as exc:
        # Pretty-print every missing / invalid field before dying
        print("\n[CONFIG ERROR] One or more required environment variables are missing or invalid:\n")
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            msg = error["msg"]
            print(f"  [X]  {loc}: {msg}")
        print(f"\n  -->  Check your .env file (expected at: {_ENV_FILE})")
        print(f"  -->  Copy .env.example to .env and fill in all required values.\n")
        sys.exit(1)


# Singleton — import this throughout the app
settings: Settings = _load_settings()
