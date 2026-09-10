"""
Team Finder schemas.

Supports Phase B6:
  - GET /api/team-finder/matches: TeamMatchesResponse, TeamMatchItem
  - POST /api/team-finder/invite: TeamInviteRequest, TeamInviteResponse
  - POST /api/team-finder/teams: TeamCreateRequest, TeamResponse, TeamMemberOut
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import TimestampedModel


# ── Phase B6: Match Finder Schemas ────────────────────────────────────────────

class TeamMatchItem(BaseModel):
    """Represents a potential teammate candidate and their compatibility metrics."""
    student_id: UUID
    name: str
    avatar_url: Optional[str] = None
    department: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    preferred_role: str
    similarity_score: float = Field(ge=0.0, le=1.0, description="Cosine similarity of profile embeddings")
    role_bonus: float = Field(ge=0.0, le=1.0, description="Bonus weight applied for complementary roles")
    match_score: float = Field(ge=0.0, le=1.0, description="Overall compatibility score (similarity + role bonus)")
    match_percentage: float = Field(ge=0.0, le=100.0, description="Match score formatted as percentage")
    is_complementary: bool = Field(description="True if candidate role differs from current student role")
    shared_skills: List[str] = Field(default_factory=list)
    complementary_skills: List[str] = Field(default_factory=list)
    recommendation_reason: str

    model_config = ConfigDict(from_attributes=True)


class TeamMatchesResponse(BaseModel):
    """Response returned by GET /api/team-finder/matches."""
    event_id: UUID
    event_title: str
    current_student_id: UUID
    current_student_name: str
    current_student_role: str
    total_candidates: int
    matches: List[TeamMatchItem]


# ── Phase B6: Team Invite Schemas ─────────────────────────────────────────────

class TeamInviteRequest(BaseModel):
    """Request payload for POST /api/team-finder/invite."""
    event_id: UUID
    invited_student_id: UUID
    team_id: Optional[UUID] = Field(default=None, description="Optional team ID; if omitted, active team will be used or created")
    role: Optional[str] = Field(default="member", description="Role offered: member | leader | observer")
    custom_message: Optional[str] = Field(default=None, description="Optional custom invite message")


class TeamInviteResponse(BaseModel):
    """Response payload for POST /api/team-finder/invite."""
    invite_id: UUID
    team_id: UUID
    team_name: str
    event_id: UUID
    inviter_id: UUID
    inviter_name: str
    invited_student_id: UUID
    invited_student_name: str
    role: str
    status: str = "pending"
    message: str
    created_at: datetime


# ── Phase B6: Team Creation & Management Schemas ──────────────────────────────

class TeamCreateRequest(BaseModel):
    """Request payload for POST /api/team-finder/teams."""
    event_id: UUID
    name: str = Field(min_length=2, max_length=100, description="Display name for the team")
    member_ids: List[UUID] = Field(default_factory=list, description="IDs of accepted members to add")
    is_open: bool = Field(default=True, description="Whether other students can freely join")


class TeamMemberOut(BaseModel):
    """A member in a team."""
    student_id: UUID
    name: str
    role: str
    status: str = "accepted"
    avatar_url: Optional[str] = None
    joined_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TeamResponse(BaseModel):
    """Response returned after team creation."""
    id: UUID
    event_id: UUID
    name: str
    created_by: UUID
    is_open: bool
    members: List[TeamMemberOut] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ── Legacy / Compatibility Schemas ────────────────────────────────────────────

class TeamFinderRequest(BaseModel):
    user_id: UUID
    opportunity_id: UUID
    required_roles: List[str] = Field(default_factory=list)
    team_size: int = Field(default=4, ge=2, le=20)
    top_k_per_role: int = Field(default=5, ge=1, le=20)


class TeamMemberSuggestion(BaseModel):
    user_id: UUID
    full_name: str
    avatar_url: Optional[str] = None
    role: str
    match_score: float = Field(ge=0.0, le=1.0)
    skills: List[str] = Field(default_factory=list)
    trust_score: float = Field(ge=0.0, le=100.0, default=0.0)


class TeamFinderResponse(BaseModel):
    opportunity_id: UUID
    suggested_team: List[TeamMemberSuggestion]


class Team(TimestampedModel):
    id: UUID
    event_id: Optional[UUID] = None
    opportunity_id: Optional[UUID] = None
    name: str
    member_ids: List[UUID] = Field(default_factory=list)
    is_open: bool = True
