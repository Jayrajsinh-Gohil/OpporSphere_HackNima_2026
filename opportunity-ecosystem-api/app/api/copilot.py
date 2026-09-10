"""
Copilot routes — /api/v1/copilot & /api/copilot

Implements Phase B8:
  - POST /api/copilot/chat: Context-grounded RAG conversation assistant with live
    opportunity/event DB retrieval, local Ollama generation, session history, and
    hallucination guard.
  - POST /api/copilot/stream: SSE streaming response.
"""

from __future__ import annotations

from typing import Union
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.auth import get_current_user
from app.models.base import APIResponse
from app.models.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotRequest,
    CopilotResponse,
)
from app.services import copilot, copilot_service

router = APIRouter(prefix="/copilot", tags=["Copilot"])


# ── Phase B8: RAG Conversational Chat ─────────────────────────────────────────

@router.post(
    "/chat",
    response_model=APIResponse[CopilotChatResponse],
    summary="Chat with the AI copilot grounded in live opportunities (RAG)",
    description=(
        "Retrieves top-5 relevant opportunities from Supabase using pgvector similarity. "
        "Constructs a grounded prompt for the local Ollama LLM with system instructions, "
        "live context, user message, and the last 3 turns of conversation history. "
        "Includes a hallucination guard that returns a safe fallback message if "
        "no relevant opportunities are found."
    ),
)
async def chat(
    body: CopilotChatRequest,
    _claims: dict = Depends(get_current_user),
):
    try:
        chat_result = await copilot.chat(body)
        return APIResponse(
            data=chat_result,
            message="Copilot response generated successfully.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot chat failed: {exc}",
        )


# ── Streaming Route ───────────────────────────────────────────────────────────

@router.post(
    "/stream",
    summary="Chat with the AI copilot (SSE streaming)",
)
async def stream_chat(
    body: CopilotRequest,
    _claims: dict = Depends(get_current_user),
):
    """Returns a text/event-stream response with token-by-token chunks."""

    async def event_generator():
        try:
            async for token in copilot_service.stream_copilot(body):
                yield f"data: {token}\n\n"
        except Exception as exc:
            yield f"data: [ERROR] {exc}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
