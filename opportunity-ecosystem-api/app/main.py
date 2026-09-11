"""
opportunity-ecosystem-api — FastAPI application entry point.

Start dev server:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Endpoints overview:
    GET  /health                                — liveness probe

    ── Auth (Supabase JWT verification)
    POST /api/v1/auth/register
    POST /api/v1/auth/login
    POST /api/v1/auth/refresh
    GET  /api/v1/auth/me

    ── Students
    GET   /api/v1/students/me                   — read own profile
    POST  /api/v1/students/me                   — create/replace own profile
    PATCH /api/v1/students/me                   — partial update own profile

    ── Opportunities
    GET   /api/v1/opportunities                 — public list (filters + pagination)
    POST  /api/v1/opportunities                 — admin: create
    GET   /api/v1/opportunities/{id}            — public: single opportunity
    PATCH /api/v1/opportunities/{id}            — admin: update
    POST  /api/v1/opportunities/{id}/events     — admin: add event
    GET   /api/v1/opportunities/{id}/events     — public: list events

    ── AI Modules
    POST /api/v1/match/
    POST /api/v1/match/opportunities
    POST /api/v1/discovery/
    POST /api/v1/copilot/chat
    POST /api/v1/copilot/stream
    GET  /api/v1/trust/{user_id}
    POST /api/v1/trust/endorse
    POST /api/v1/trust/rate
    POST /api/v1/team-finder/
    POST /api/v1/content-gen/
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import socket

# Prefer IPv4 over blackholed IPv6 routes to prevent 30-90s connection timeouts on external requests
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_preferred_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if family == 0:
        family = socket.AF_INET
    return _orig_getaddrinfo(host, port, family, type, proto, flags)
socket.getaddrinfo = _ipv4_preferred_getaddrinfo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.api import (
    admin,
    auth,
    content_gen,
    copilot,
    discovery,
    match,
    opportunities,
    students,
    team_finder,
    trust,
)
from app.core.config import settings


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    logger.info(f"🚀 Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    async def _async_warmup():
        # Validate Supabase connectivity in background
        try:
            from app.core.supabase_client import supabase_admin
            await asyncio.to_thread(lambda: supabase_admin.table("students").select("id").limit(1).execute())
            logger.info("✅ Supabase connection verified (students table).")
        except Exception as exc:
            logger.warning(f"⚠️  Supabase background check notice: {exc}")

        # Pre-warm local SentenceTransformer model in background thread
        try:
            from app.ml.embeddings import get_local_embedder
            logger.info("🔄 Pre-warming SentenceTransformer model (all-MiniLM-L6-v2)...")
            embedder = get_local_embedder()
            await asyncio.to_thread(embedder.load_model)
            logger.info("✅ SentenceTransformer (all-MiniLM-L6-v2) loaded and ready.")
        except Exception as exc:
            logger.warning(f"⚠️  Could not pre-warm sentence-transformers model: {exc}")

    # Launch warmup in background so FastAPI starts listening and serving HTTP traffic instantly
    asyncio.create_task(_async_warmup())

    yield  # Application runs immediately without startup delays

    logger.info("🛑 Shutting down OpporSphere API.")


# ── Application factory ────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered opportunity discovery, matching, team-building, "
            "trust scoring, and content generation platform."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health endpoint ───────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health():
        return JSONResponse(
            content={
                "status": "ok",
                "app": settings.APP_NAME,
                "env": settings.APP_ENV,
                "version": "1.0.0",
            }
        )

    # ── API v1 routers ──────────────────────────────────────────────────────────────
    prefix = "/api/v1"
    # Admin
    app.include_router(admin.router,         prefix=prefix)
    # Auth
    app.include_router(auth.router,          prefix=prefix)
    # Core CRUD (B2)
    app.include_router(students.router,      prefix=prefix)
    app.include_router(opportunities.router, prefix=prefix)
    # AI modules
    app.include_router(match.router,         prefix=prefix)
    app.include_router(discovery.router,     prefix=prefix)
    app.include_router(copilot.router,       prefix=prefix)
    app.include_router(trust.router,         prefix=prefix)
    app.include_router(team_finder.router,   prefix=prefix)
    app.include_router(content_gen.router,   prefix=prefix)

    # Direct /api prefix aliases for frontend and prompt compatibility
    app.include_router(admin.router,         prefix="/api")
    app.include_router(auth.router,          prefix="/api")
    app.include_router(students.router,      prefix="/api")
    app.include_router(opportunities.router, prefix="/api")
    app.include_router(match.router,         prefix="/api")
    app.include_router(trust.router,         prefix="/api")
    app.include_router(content_gen.router,   prefix="/api")
    app.include_router(team_finder.router,   prefix="/api")
    app.include_router(discovery.router,     prefix="/api")
    app.include_router(copilot.router,       prefix="/api")

    return app


app = create_app()
