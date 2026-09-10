"""
Core configuration — reads all environment variables via pydantic-settings.
All other modules import `settings` from here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "OpporSphere API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Accepts a comma-separated string from .env  →  splits into a list
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    # ── Supabase ─────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    # Found in: Supabase Dashboard → Settings → API → JWT Settings → JWT Secret
    SUPABASE_JWT_SECRET: str = ""

    # ── Gemini (default LLM provider) ────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ── Ollama (optional local LLM provider) ─────────────────────────────────
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # ── LLM Provider ─────────────────────────────────────────────────────────
    # Default fallback if Supabase app_settings table has no override.
    # Values: "gemini" | "ollama"
    LLM_PROVIDER: str = "gemini"

    # ── JWT ──────────────────────────────────────────────────────────────────
    # Supabase always uses HS256 for its project JWTs
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — import and call once per process."""
    return Settings()


# Convenience shortcut used throughout the codebase
settings: Settings = get_settings()
