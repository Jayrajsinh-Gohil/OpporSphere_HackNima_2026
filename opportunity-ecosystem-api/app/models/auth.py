"""
Auth-related Pydantic schemas.
Maps to Supabase `auth.users` + a `profiles` table.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.base import TimestampedModel


# ── Request schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class GoogleSessionRequest(BaseModel):
    """
    Body for POST /auth/google/session.
    After Google OAuth, the frontend extracts these tokens from the URL fragment
    (via Supabase JS SDK) and sends them here to receive app-level JWTs.
    """
    supabase_access_token: str = Field(..., description="Supabase access_token from OAuth URL fragment")
    supabase_refresh_token: str = Field(..., description="Supabase refresh_token from OAuth URL fragment")



# ── Response schemas ───────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserProfile(TimestampedModel):
    id: UUID
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    role: str = "user"  # user | admin | moderator
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
