"""
Copilot service — AI assistant for opportunity-related conversations.
Maintains session context and supports streaming responses.
"""

from __future__ import annotations

from typing import AsyncIterator, List



from app.core.supabase_client import supabase_admin
from app.ml.llm_client import get_llm_client
from app.models.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CopilotMessage,
    CopilotRequest,
    CopilotResponse,
)
from app.services.copilot import (
    append_session_turn,
    build_copilot_prompt,
    chat,
    clear_session,
    get_session_history,
    retrieve_grounding_opportunities,
)

__all__ = [
    "chat",
    "chat_with_copilot",
    "stream_copilot",
    "retrieve_grounding_opportunities",
    "build_copilot_prompt",
    "get_session_history",
    "append_session_turn",
    "clear_session",
]

_SYSTEM_PROMPT = """
You are the OpporSphere Copilot — an expert AI assistant that helps
users discover opportunities, craft applications, build teams, and grow their
professional network.

Guidelines:
- Be concise, actionable, and encouraging.
- If the user asks about a specific opportunity, reference the provided context.
- Suggest concrete next steps at the end of each reply.
- Keep replies under 300 words unless more detail is explicitly requested.
"""


def _to_messages(
    history: List[CopilotMessage],
) -> List[dict]:
    return [{"role": m.role, "content": m.content} for m in history]


async def chat_with_copilot(request: CopilotRequest) -> CopilotResponse:
    """Non-streaming copilot response."""
    llm = await get_llm_client()

    # Enrich system prompt with opportunity context if provided
    system = _SYSTEM_PROMPT
    if request.context:
        system += f"\n\nCurrent context: {request.context}"

    history = _to_messages(request.history)

    reply = await llm.chat(
        user_prompt=request.message,
        system_prompt=system,
        history=history,
        temperature=0.7,
        max_tokens=600,
    )

    # Extract suggested actions (simple heuristic: bullet lines)
    suggested_actions = [
        line.lstrip("- •*").strip()
        for line in reply.splitlines()
        if line.strip().startswith(("-", "•", "*"))
    ][:3]

    return CopilotResponse(
        reply=reply,
        suggested_actions=suggested_actions,
    )


async def stream_copilot(request: CopilotRequest) -> AsyncIterator[str]:
    """Streaming copilot response — yields token chunks."""
    llm = await get_llm_client()
    system = _SYSTEM_PROMPT
    if request.context:
        system += f"\n\nCurrent context: {request.context}"

    async for token in llm.stream(
        user_prompt=request.message,
        system_prompt=system,
        temperature=0.7,
        max_tokens=600,
    ):
        yield token
