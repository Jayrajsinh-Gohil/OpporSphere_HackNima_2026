"""
Supabase client factory.

Exports two pre-built clients:
  - `supabase`       — anon-key client  (safe for end-user operations)
  - `supabase_admin` — service-role client  (server-side only, bypass RLS)

Both are lazy singletons; they are created once on first import.
"""

from __future__ import annotations

from functools import lru_cache

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def _build_anon_client() -> Client:
    url = settings.SUPABASE_URL or "https://placeholder-project.supabase.co"
    key = settings.SUPABASE_ANON_KEY or "placeholder-anon-key"
    try:
        return create_client(url, key)
    except Exception as exc:
        logger.warning(f"Could not initialize Supabase anon client: {exc}")
        return None


@lru_cache
def _build_admin_client() -> Client:
    url = settings.SUPABASE_URL or "https://placeholder-project.supabase.co"
    key = settings.SUPABASE_SERVICE_ROLE_KEY or "placeholder-service-role-key"
    try:
        return create_client(url, key)
    except Exception as exc:
        logger.warning(f"Could not initialize Supabase admin client: {exc}")
        return None


# ── Public singletons ─────────────────────────────────────────────────────────
supabase: Client = _build_anon_client()
supabase_admin: Client = _build_admin_client()
