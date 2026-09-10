"""
FastAPI dependencies — reusable injectable functions.

Key exports:
  - get_current_student()   → verifies Supabase JWT, returns StudentProfile
  - require_admin()         → same as above but checks admins table in Supabase DB
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from loguru import logger

from app.core.config import settings
from app.core.supabase_client import supabase_admin
from app.models.student import StudentProfile

# ── Bearer scheme ──────────────────────────────────────────────────────────────
_bearer = HTTPBearer(auto_error=True)


# ── Token verification ─────────────────────────────────────────────────────────

def _decode_supabase_jwt(token: str) -> dict:
    """
    Verify a Supabase-issued JWT using the project's JWT secret.

    Supabase tokens:
      - Algorithm : HS256
      - Issuer    : https://<project-ref>.supabase.co/auth/v1
      - Subject   : auth.users.id  (UUID string)
      - email     : available in the token claims

    The JWT secret is found in:
      Supabase Dashboard → Settings → API → JWT Settings → JWT Secret
    """
    if not settings.SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured on the server.",
        )
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},   # Supabase doesn't set 'aud' by default
        )
        return payload
    except JWTError as exc:
        logger.debug(f"JWT verification failed: {exc}")
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

    if resp.data:
        return StudentProfile(**resp.data)

    # ── Auto-create a minimal profile on first authenticated request ──────────
    logger.info(f"Auto-creating student profile for {user_id}")
    insert_resp = (
        supabase_admin.table("students")
        .insert({"id": user_id, "email": email, "name": email.split("@")[0]})
        .execute()
    )
    if not insert_resp.data:
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
    try:
        resp = (
            supabase_admin.table("admins")
            .select("id")
            .eq("email", email.lower())
            .eq("is_active", True)
            .maybe_single()
            .execute()
        )
        return bool(resp.data)
    except Exception as exc:
        logger.warning(f"Admin check failed for {email}: {exc}")
        return False


# ── Public dependencies ────────────────────────────────────────────────────────

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
CurrentStudent = Annotated[StudentProfile, Depends(get_current_student)]
AdminStudent   = Annotated[StudentProfile, Depends(require_admin)]
