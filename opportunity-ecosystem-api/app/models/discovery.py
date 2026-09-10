"""
Discovery schemas.

Supports:
  - Phase B7: AI Smart Discovery natural-language search (SmartSearchRequest, SmartSearchResponse)
  - Legacy opportunity discovery and tag-based filtering (DiscoveryRequest, DiscoveryResponse)
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Phase B7: AI Smart Discovery Schemas ──────────────────────────────────────

class SmartSearchRequest(BaseModel):
    """Payload for POST /api/discovery/search."""
    query: str = Field(min_length=1, max_length=500, description="Natural language opportunity query")
    top_k: int = Field(default=10, ge=1, le=50, description="Maximum number of matched opportunities")


class ExtractedFilters(BaseModel):
    """Structured filters extracted via spaCy EntityRuler."""
    domain: Optional[str] = Field(default=None, description="Mapped domain (technology, science, environment, etc.)")
    location: Optional[str] = Field(default=None, description="Location constraint (e.g. Bengaluru, Online, Remote)")
    department: Optional[str] = Field(default=None, description="Student type or department (e.g. Computer Science, Undergrad)")
    opportunity_type: Optional[str] = Field(default=None, description="Type: hackathon, internship, workshop, competition, etc.")
    deadline_from: Optional[date] = Field(default=None, description="Start date of deadline window")
    deadline_to: Optional[date] = Field(default=None, description="End date of deadline window")
    raw_entities: Dict[str, List[str]] = Field(default_factory=dict, description="Raw named entities detected by spaCy")

    model_config = ConfigDict(from_attributes=True)


class DiscoveredOpportunityItem(BaseModel):
    """A matched opportunity returned by natural language discovery."""
    id: UUID
    title: str
    description: str
    domain: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    organizer: Optional[str] = None
    deadline: Optional[str] = None
    trust_score: int = Field(default=0, ge=0, le=100)
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.0, description="Relevance score or similarity match")
    match_reason: str

    model_config = ConfigDict(from_attributes=True)


class SmartSearchResponse(BaseModel):
    """Response returned by POST /api/discovery/search."""
    query: str
    search_mode: str = Field(description="Search strategy used: structured_filter | semantic_fallback | hybrid")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Entity extraction confidence score")
    filters_applied: ExtractedFilters
    total: int
    results: List[DiscoveredOpportunityItem]

    model_config = ConfigDict(from_attributes=True)


# ── Legacy / Discovery Feed Schemas ───────────────────────────────────────────

class DiscoveryRequest(BaseModel):
    user_id: Optional[UUID] = None
    query: Optional[str] = None          # free-text search
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class DiscoveredOpportunity(BaseModel):
    id: UUID
    title: str
    description: str
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0, default=0.0)
    source_url: Optional[str] = None
    deadline: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DiscoveryResponse(BaseModel):
    results: List[DiscoveredOpportunity]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
