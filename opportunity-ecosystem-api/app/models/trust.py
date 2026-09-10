"""
Trust & reputation schemas.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.base import TimestampedModel


class TrustScore(TimestampedModel):
    user_id: UUID
    overall_score: float = Field(ge=0.0, le=100.0, default=0.0)
    endorsements: int = 0
    completed_opportunities: int = 0
    peer_ratings_avg: float = Field(ge=0.0, le=5.0, default=0.0)
    badges: List[str] = Field(default_factory=list)


class EndorsementCreate(BaseModel):
    endorsed_user_id: UUID
    skill: str
    note: Optional[str] = Field(default=None, max_length=500)


class RatingCreate(BaseModel):
    rated_user_id: UUID
    opportunity_id: UUID
    rating: float = Field(ge=1.0, le=5.0)
    review: Optional[str] = Field(default=None, max_length=1000)
