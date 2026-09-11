"""
FastAPI dependencies — reusable injectable functions.

Key exports:
  - get_current_student()   → verifies Supabase JWT, returns StudentProfile
  - require_admin()         → same as above but checks admins table in Supabase DB
"""

from __future__ import annotations

import json
import urllib.request
from typing import Annotated, Any, Dict, List, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.jwk import construct
from loguru import logger

from app.core.config import settings
from app.core.supabase_client import supabase_admin
from app.models.student import StudentProfile

# ── Bearer scheme ──────────────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=True)

# In-memory JWKS cache for asymmetric Supabase tokens (ES256/RS256)
_JWKS_CACHE: Dict[str, Any] = {}


def _get_supabase_jwks(force_refresh: bool = False) -> List[dict]:
    """Fetch and cache public signing keys from Supabase project JWKS."""
    global _JWKS_CACHE
    if not _JWKS_CACHE.get("keys") or force_refresh:
        if not settings.SUPABASE_URL:
            return []
        try:
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            headers = {"User-Agent": "OpporSphere-API/1.0"}
            if settings.SUPABASE_ANON_KEY:
                headers["apikey"] = settings.SUPABASE_ANON_KEY
            req = urllib.request.Request(jwks_url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as res:
                _JWKS_CACHE = json.loads(res.read().decode())
                logger.info(f"Loaded {len(_JWKS_CACHE.get('keys', []))} JWKS key(s) from Supabase.")
        except Exception as exc:
            logger.warning(f"Could not fetch Supabase JWKS from {settings.SUPABASE_URL}: {exc}")
    return _JWKS_CACHE.get("keys", [])


# ── Token verification ─────────────────────────────────────────────────────────

def _decode_supabase_jwt(token: str) -> dict:
    """
    Verify a Supabase-issued JWT.
    Supports:
      1. Asymmetric algorithms (ES256, RS256, ES384, ES512) via Supabase project JWKS.
      2. Symmetric algorithm (HS256) via SUPABASE_JWT_SECRET.
      3. Authoritative verification fallback via Supabase GoTrue Auth API (get_user).
    """
    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg", "HS256")
        kid = header.get("kid")
    except Exception as exc:
        logger.debug(f"Could not read JWT header: {exc}")
        alg = "HS256"
        kid = None

    # 1. Asymmetric algorithms (ES256, RS256, ES384, ES512) using Supabase JWKS
    if alg in ("ES256", "RS256", "ES384", "ES512"):
        keys = _get_supabase_jwks()
        target_keys = [k for k in keys if not kid or k.get("kid") == kid]
        if not target_keys and keys:
            keys = _get_supabase_jwks(force_refresh=True)
            target_keys = [k for k in keys if not kid or k.get("kid") == kid] or keys

        for key_dict in target_keys:
            try:
                parsed_key = construct(key_dict)
                payload = jwt.decode(
                    token,
                    parsed_key,
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
                return payload
            except Exception as exc:
                logger.debug(f"JWKS key decode attempt failed: {exc}")

    # 2. Symmetric HS256 algorithm using SUPABASE_JWT_SECRET
    if (alg == "HS256" or not alg) and settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except JWTError as exc:
            logger.debug(f"HS256 verification failed: {exc}")

    # 3. Direct verification via Supabase GoTrue Auth API (handles any valid Supabase token)
    try:
        user_resp = supabase_admin.auth.get_user(token)
        if user_resp and user_resp.user:
            user = user_resp.user
            logger.debug(f"Verified token via Supabase Auth API for user {user.id}")
            return {
                "sub": str(user.id),
                "email": user.email or "",
                "role": user.role or "authenticated",
                "app_metadata": user.app_metadata or {},
                "user_metadata": user.user_metadata or {},
            }
    except Exception as exc:
        logger.debug(f"Supabase auth.get_user verification failed: {exc}")

    logger.warning("All Supabase JWT verification attempts failed for incoming token.")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


# ── Student profile loader ─────────────────────────────────────────────────────

async def _load_student(user_id: str, email: str) -> StudentProfile:
    """
    Fetch (or auto-create) a student profile row from Supabase.
    Auto-creation ensures the profile exists even on first login before
    the student calls POST /students/me.
    """
    resp = (
        supabase_admin.table("students")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )

    if resp and resp.data:
        return StudentProfile(**resp.data)

    # ── Auto-create a minimal profile on first authenticated request ──────────
    logger.info(f"Auto-creating student profile for {user_id}")
    clean_email = email.strip() if email else ""
    insert_resp = (
        supabase_admin.table("students")
        .insert({"id": user_id, "email": clean_email, "name": clean_email.split("@")[0] if clean_email else "Student"})
        .execute()
    )
    if not insert_resp or not insert_resp.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create student profile.",
        )
    return StudentProfile(**insert_resp.data[0])


# ── Admin check via Supabase DB ────────────────────────────────────────────────

async def _is_admin(email: str) -> bool:
    """
    Check whether the given email exists in the `admins` table.
    Admins are managed via Supabase dashboard (not .env).
    """
    if not email:
        return False
    try:
        resp = (
            supabase_admin.table("admins")
            .select("id")
            .eq("email", email.strip().lower())
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return bool(resp and resp.data)
    except Exception as exc:
        logger.warning(f"Admin check failed for {email}: {exc}")
        return False


# ── Public dependencies ────────────────────────────────────────────────────────
_optional_bearer = HTTPBearer(auto_error=False)


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> StudentProfile:
    """
    Dependency: verify the Supabase JWT and return the authenticated student.

    Usage:
        @router.get("/me")
        async def me(student: StudentProfile = Depends(get_current_student)):
            ...
    """
    claims = _decode_supabase_jwt(credentials.credentials)

    user_id: str | None = claims.get("sub")
    email: str = claims.get("email", "")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim.",
        )

    return await _load_student(user_id, email)


async def get_optional_current_student(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_optional_bearer),
) -> Optional[StudentProfile]:
    """Dependency: returns student if valid token provided, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        claims = _decode_supabase_jwt(credentials.credentials)
        user_id: str | None = claims.get("sub")
        email: str = claims.get("email", "")
        if not user_id:
            return None
        return await _load_student(user_id, email)
    except Exception:
        return None


async def require_admin(
    student: StudentProfile = Depends(get_current_student),
) -> StudentProfile:
    """
    Dependency: same as get_current_student but also enforces admin role.

    Admins are stored in the `admins` Supabase table.
    Add/remove admins via Supabase dashboard without restarting the server.
    """
    if not await _is_admin(student.email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required. Contact a super_admin to be added to the admins table.",
        )
    return student


# ── Type aliases for cleaner route signatures ──────────────────────────────────
CurrentStudent  = Annotated[StudentProfile, Depends(get_current_student)]
OptionalStudent = Annotated[Optional[StudentProfile], Depends(get_optional_current_student)]
AdminStudent    = Annotated[StudentProfile, Depends(require_admin)]
