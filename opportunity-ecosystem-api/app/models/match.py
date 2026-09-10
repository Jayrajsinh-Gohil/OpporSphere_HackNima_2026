"""
Opportunity / Match schemas.
Maps to Supabase `opportunities` and `matches` tables.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.base import TimestampedModel


class MatchRequest(BaseModel):
    user_id: UUID
    opportunity_id: Optional[UUID] = None   # if None → match across all
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.5, ge=0.0, le=1.0)


class MatchResult(BaseModel):
    opportunity_id: UUID
    title: str
    description: str
    match_score: float = Field(ge=0.0, le=1.0)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None


class MatchResponse(BaseModel):
    user_id: UUID
    results: List[MatchResult]
    total: int


class Opportunity(TimestampedModel):
    id: UUID
    title: str
    description: str
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    deadline: Optional[str] = None  # ISO date string
    is_active: bool = True
    embedding: Optional[List[float]] = None  # stored but not serialised to client

    model_config = ConfigDict(from_attributes=True)


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=5)
    description: str = Field(min_length=20)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    source_url: Optional[str] = None
    deadline: Optional[str] = None


# ── Phase B3: Recommendations schemas ─────────────────────────────────────────

class RecommendationItem(BaseModel):
    id: UUID
    title: str
    description: str
    domain: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    deadline: Optional[str] = None
    trust_score: int = Field(default=0, ge=0, le=100)
    similarity: float = Field(ge=0.0, le=1.0)
    match_relevance_pct: float = Field(ge=0.0, le=100.0)  # similarity score as match relevance %
    is_fallback: bool = False
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RecommendationsResponse(BaseModel):
    student_id: UUID
    has_profile_embedding: bool
    has_interaction_history: bool
    recommendations: List[RecommendationItem]
    total: int
