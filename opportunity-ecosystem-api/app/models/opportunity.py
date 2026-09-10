"""
Pydantic schemas matching the `opportunities`, `events`, and `trust_scores` tables.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.base import TimestampedModel


# ── ENUMs (mirror DB enums) ────────────────────────────────────────────────────

class OpportunityType(str, Enum):
    HACKATHON   = "hackathon"
    INTERNSHIP  = "internship"
    WORKSHOP    = "workshop"
    COMPETITION = "competition"
    FELLOWSHIP  = "fellowship"
    GRANT       = "grant"
    OTHER       = "other"


class OpportunityDomain(str, Enum):
    TECHNOLOGY    = "technology"
    SCIENCE       = "science"
    ARTS          = "arts"
    BUSINESS      = "business"
    SOCIAL_IMPACT = "social_impact"
    HEALTH        = "health"
    EDUCATION     = "education"
    ENVIRONMENT   = "environment"
    OTHER         = "other"


class EventStatus(str, Enum):
    UPCOMING  = "upcoming"
    OPEN      = "open"
    CLOSED    = "closed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# ── Opportunity schemas ────────────────────────────────────────────────────────

class OpportunityCreate(BaseModel):
    title: str = Field(min_length=5, max_length=255)
    description: str = Field(min_length=20)
    domain: OpportunityDomain = OpportunityDomain.OTHER
    type: OpportunityType = OpportunityType.OTHER
    eligibility: Optional[str] = None
    deadline: Optional[date] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    source_url: Optional[str] = None


class OpportunityUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=255)
    description: Optional[str] = None
    domain: Optional[OpportunityDomain] = None
    type: Optional[OpportunityType] = None
    eligibility: Optional[str] = None
    deadline: Optional[date] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None


class OpportunityOut(TimestampedModel):
    id: UUID
    title: str
    description: str
    domain: OpportunityDomain
    type: OpportunityType
    eligibility: Optional[str] = None
    deadline: Optional[date] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    source_url: Optional[str] = None
    is_active: bool = True
    # embedding excluded from API responses

    model_config = ConfigDict(from_attributes=True)


class OpportunitySummary(OpportunityOut):
    """Enriched view including trust signals (from opportunity_summary view)."""
    trust_score: int = 0
    is_duplicate: bool = False
    quality_flags: Dict[str, Any] = Field(default_factory=dict)
    event_count: int = 0


# ── Event schemas ──────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    opportunity_id: UUID
    status: EventStatus = EventStatus.UPCOMING
    registration_link: Optional[str] = None
    extra_details: Dict[str, Any] = Field(default_factory=dict)


class EventOut(TimestampedModel):
    id: UUID
    opportunity_id: UUID
    status: EventStatus
    registration_link: Optional[str] = None
    extra_details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


# ── Trust score schemas ────────────────────────────────────────────────────────

class TrustScoreOut(BaseModel):
    opportunity_id: UUID
    score: int = Field(ge=0, le=100)
    duplicate_flag: bool = False
    quality_flags: Dict[str, Any] = Field(default_factory=dict)
    computed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
