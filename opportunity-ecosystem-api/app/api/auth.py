"""
Auth routes — /api/v1/auth
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.models.auth import (
    ChangePasswordRequest,
    GoogleSessionRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserProfile,
)
from app.models.base import APIResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])
bearer_scheme = HTTPBearer()


# ── Dependency: current user from JWT ─────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract and validate the JWT from Authorization header."""
    try:
        claims = auth_service.decode_token(credentials.credentials)
        return claims
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Email / Password Endpoints ─────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user with email and password",
)
async def register(body: RegisterRequest):
    try:
        tokens = await auth_service.register_user(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return APIResponse(data=tokens, message="User registered successfully.")


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    summary="Login with email and password",
)
async def login(body: LoginRequest):
    try:
        tokens = await auth_service.login_user(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return APIResponse(data=tokens, message="Login successful.")


@router.post(
    "/refresh",
    response_model=APIResponse[TokenResponse],
    summary="Refresh access token",
)
async def refresh(body: RefreshTokenRequest):
    try:
        tokens = await auth_service.refresh_access_token(body.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return APIResponse(data=tokens, message="Token refreshed.")


# ── Google OAuth Endpoints ─────────────────────────────────────────────────────

@router.get(
    "/google",
    summary="Initiate Google OAuth login",
    description=(
        "Returns the Google OAuth URL. "
        "Frontend should redirect the user to this URL. "
        "After signing in, Google redirects back through Supabase, "
        "then to your frontend with tokens in the URL fragment."
    ),
)
async def google_oauth_redirect(
    redirect_url: Optional[str] = Query(
        default=None,
        description="URL to redirect after OAuth (defaults to Supabase callback)"
    ),
):
    """Return Google OAuth URL for the frontend to redirect to."""
    try:
        url = auth_service.get_google_oauth_url(redirect_url)
        return APIResponse(data={"url": url}, message="Redirect to this URL to sign in with Google.")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post(
    "/google/session",
    response_model=APIResponse[TokenResponse],
    summary="Exchange Supabase Google OAuth session for app JWT",
    description=(
        "After Google OAuth completes, the frontend receives Supabase access_token and "
        "refresh_token from the URL fragment. Send them here to get app-level JWTs."
    ),
)
async def google_session_exchange(body: GoogleSessionRequest):
    """Exchange Supabase OAuth tokens for app-level JWTs."""
    try:
        tokens = await auth_service.exchange_google_session(
            body.supabase_access_token,
            body.supabase_refresh_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return APIResponse(data=tokens, message="Google login successful.")


# ── Profile ────────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=APIResponse[UserProfile],
    summary="Get current user profile",
)
async def me(claims: dict = Depends(get_current_user)):
    from uuid import UUID
    profile = await auth_service.get_user_profile(UUID(claims["sub"]))
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found.")
    return APIResponse(data=profile)
