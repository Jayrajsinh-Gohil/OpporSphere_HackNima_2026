"""
Auth service — register, login, refresh, Google OAuth, JWT helpers.
Delegates credential management to Supabase Auth.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from loguru import logger
from supabase import AuthApiError

from app.core.config import settings
from app.core.supabase_client import supabase, supabase_admin
from app.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile


# ── JWT helpers ────────────────────────────────────────────────────────────────

def _create_access_token(payload: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {**payload, "exp": expire, "type": "access"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _create_refresh_token(payload: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    return jwt.encode(
        {**payload, "exp": expire, "type": "refresh"},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT; raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ── Email/Password auth ────────────────────────────────────────────────────────

async def register_user(data: RegisterRequest) -> TokenResponse:
    """Create a new user via Supabase Auth and seed their profile."""
    logger.info(f"Registering user: {data.email}")
    try:
        auth_response = supabase.auth.sign_up(
            {"email": data.email, "password": data.password}
        )
    except AuthApiError as exc:
        logger.error(f"Supabase sign-up error: {exc}")
        raise ValueError(str(exc)) from exc

    user = auth_response.user
    if not user:
        raise ValueError("Registration failed — no user returned.")

    # Seed profiles table
    supabase_admin.table("profiles").upsert(
        {
            "id": str(user.id),
            "email": data.email,
            "full_name": data.full_name,
        }
    ).execute()

    payload = {"sub": str(user.id), "email": data.email}
    return TokenResponse(
        access_token=_create_access_token(payload),
        refresh_token=_create_refresh_token(payload),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def login_user(data: LoginRequest) -> TokenResponse:
    """Authenticate via Supabase Auth and return JWT tokens."""
    logger.info(f"Login attempt: {data.email}")
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {"email": data.email, "password": data.password}
        )
    except AuthApiError as exc:
        raise ValueError("Invalid credentials.") from exc

    user = auth_response.user
    if not user:
        raise ValueError("Authentication failed.")

    payload = {"sub": str(user.id), "email": data.email}
    return TokenResponse(
        access_token=_create_access_token(payload),
        refresh_token=_create_refresh_token(payload),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Issue a new access token from a valid refresh token."""
    try:
        claims = decode_token(refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError("Token is not a refresh token.")
    except JWTError as exc:
        raise ValueError("Invalid or expired refresh token.") from exc

    payload = {"sub": claims["sub"], "email": claims["email"]}
    return TokenResponse(
        access_token=_create_access_token(payload),
        refresh_token=_create_refresh_token(payload),  # rotate
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── Google OAuth ───────────────────────────────────────────────────────────────

def get_google_oauth_url(redirect_url: Optional[str] = None) -> str:
    """
    Generate the Google OAuth redirect URL via Supabase.

    Steps:
      1. Backend returns this URL to the frontend.
      2. Frontend redirects the user to this URL.
      3. User signs in with Google.
      4. Google redirects to Supabase callback → Supabase issues session.
      5. Supabase redirects to frontend with access_token in URL fragment.

    The frontend then calls Supabase JS SDK to extract the session:
        supabase.auth.getSession()
    """
    opts = {"provider": "google"}
    if redirect_url:
        opts["redirect_to"] = redirect_url

    try:
        response = supabase.auth.sign_in_with_oauth(opts)
        return response.url
    except Exception as exc:
        logger.error(f"Failed to get Google OAuth URL: {exc}")
        raise ValueError(f"Could not generate Google OAuth URL: {exc}") from exc


async def exchange_google_session(access_token: str, refresh_token: str) -> TokenResponse:
    """
    Exchange a Supabase OAuth session (access + refresh tokens from URL fragment)
    for our own app JWT tokens.

    The frontend extracts these tokens from the URL after Google redirect and
    sends them to this endpoint to receive app-level JWTs.
    """
    try:
        # Set the session in Supabase client to validate it
        session = supabase.auth.set_session(access_token, refresh_token)
        user = session.user
        if not user:
            raise ValueError("No user in session.")
    except Exception as exc:
        raise ValueError(f"Invalid Supabase session tokens: {exc}") from exc

    email = user.email or ""
    user_id = str(user.id)

    # Ensure profile exists
    supabase_admin.table("profiles").upsert(
        {
            "id": user_id,
            "email": email,
            "full_name": user.user_metadata.get("full_name", email.split("@")[0]),
            "avatar_url": user.user_metadata.get("avatar_url"),
        }
    ).execute()

    logger.info(f"Google OAuth login: {email}")
    payload = {"sub": user_id, "email": email}
    return TokenResponse(
        access_token=_create_access_token(payload),
        refresh_token=_create_refresh_token(payload),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── Profile ────────────────────────────────────────────────────────────────────

async def get_user_profile(user_id: UUID) -> Optional[UserProfile]:
    """Fetch a user's profile from the `profiles` table."""
    result = (
        supabase_admin.table("profiles")
        .select("*")
        .eq("id", str(user_id))
        .single()
        .execute()
    )
    if not result.data:
        return None
    return UserProfile(**result.data)
