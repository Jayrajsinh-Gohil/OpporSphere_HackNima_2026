"""
Pydantic schemas matching the real `students` Supabase table.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.base import TimestampedModel


# ── Request schemas ────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    department: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    career_goals: Optional[str] = None
    preferred_role: Optional[str] = None
    avatar_url: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    department: Optional[str] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    career_goals: Optional[str] = None
    preferred_role: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Response schemas ───────────────────────────────────────────────────────────

class StudentProfile(TimestampedModel):
    id: UUID
    name: str
    email: EmailStr
    department: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    career_goals: Optional[str] = None
    preferred_role: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True

    # embedding is intentionally excluded from API responses
    model_config = ConfigDict(from_attributes=True)


class StudentPublic(BaseModel):
    """Minimal public view — used in team suggestions etc."""
    id: UUID
    name: str
    department: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    avatar_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
