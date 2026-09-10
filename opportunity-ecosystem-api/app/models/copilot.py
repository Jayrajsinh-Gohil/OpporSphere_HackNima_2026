"""
Copilot / AI Assistant schemas.

Supports:
  - Phase B8: AI Student Copilot (RAG) (CopilotChatRequest, CopilotChatResponse, OpportunitySourceCitation)
  - Legacy copilot schemas (CopilotRequest, CopilotResponse, CopilotMessage)
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# ── Phase B8: RAG Copilot Schemas ─────────────────────────────────────────────

class CopilotChatRequest(BaseModel):
    """Payload for POST /api/copilot/chat."""
    session_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Conversation session identifier (preserves up to 3 turns of context)",
    )
    message: str = Field(min_length=1, max_length=4096, description="User question or prompt")


class OpportunitySourceCitation(BaseModel):
    """Citation metadata for an opportunity retrieved from the live DB."""
    id: UUID
    title: str
    domain: Optional[str] = None
    type: Optional[str] = None
    location: Optional[str] = None
    deadline: Optional[str] = None
    similarity: float = Field(ge=0.0, le=1.0, default=0.0)

    model_config = ConfigDict(from_attributes=True)


class CopilotChatResponse(BaseModel):
    """Response returned by POST /api/copilot/chat."""
    session_id: str
    answer: str = Field(description="Context-grounded assistant answer")
    source_opportunity_ids: List[UUID] = Field(
        default_factory=list,
        description="IDs of source opportunities used for UI citation",
    )
    sources: List[OpportunitySourceCitation] = Field(
        default_factory=list,
        description="Detailed citation list for UI cards",
    )
    retrieval_guard_triggered: bool = Field(
        default=False,
        description="True if retrieval found no relevant opportunities and safe fallback was returned",
    )

    model_config = ConfigDict(from_attributes=True)


# ── Legacy Copilot Schemas ────────────────────────────────────────────────────

class CopilotMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str


class CopilotRequest(BaseModel):
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=4096)
    context: Optional[str] = None
    history: List[CopilotMessage] = Field(default_factory=list)
    stream: bool = False


class CopilotResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
