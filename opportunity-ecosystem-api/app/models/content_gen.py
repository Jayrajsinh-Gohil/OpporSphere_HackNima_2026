"""
Content Generation schemas.
AI-generated cover letters, proposals, summaries, etc.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    COVER_LETTER = "cover_letter"
    PROPOSAL = "proposal"
    SUMMARY = "summary"
    COLD_EMAIL = "cold_email"
    BIO = "bio"


class ContentGenRequest(BaseModel):
    user_id: UUID
    content_type: ContentType
    opportunity_id: Optional[UUID] = None
    additional_context: Optional[str] = Field(default=None, max_length=2000)
    tone: str = Field(default="professional", pattern="^(professional|casual|formal|friendly)$")
    max_words: int = Field(default=300, ge=50, le=1000)


class ContentGenResponse(BaseModel):
    content_type: ContentType
    generated_text: str
    word_count: int
    opportunity_id: Optional[UUID] = None


# ── Phase B5: Content Generation via Ollama schemas ───────────────────────────

class GenerationType(str, Enum):
    SUMMARY = "summary"
    NOTIFICATION = "notification"
    TEAM_INVITE = "team_invite"
    BIO = "bio"


class ContentGenerateRequest(BaseModel):
    type: GenerationType = Field(description="Content generation type: summary, notification, team_invite, or bio")
    input_data: dict = Field(default_factory=dict, description="Input parameters required for the selected type")


class ContentGenerateResponse(BaseModel):
    type: GenerationType
    generated_content: str
    structured_data: Optional[dict] = None
    model: str = "llama3.2:3b"
