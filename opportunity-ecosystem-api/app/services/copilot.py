"""
Copilot service — AI Student Copilot with Retrieval-Augmented Generation (Phase B8).

Implements:
  1. Vector similarity search over live opportunities and events (top-5).
  2. Hallucination guard: returns a grounded fallback message if retrieval finds nothing relevant.
  3. Context-grounded prompt engineering for local Ollama LLM (llama3.2:3b).
  4. Multi-turn conversation history tracking (last 3 turns per session).
  5. Source opportunity IDs returned for citation in UI.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_embedder
from app.models.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    OpportunitySourceCitation,
)

SYSTEM_INSTRUCTIONS = (
    "You are a helpful assistant for a student opportunity platform. "
    "Answer ONLY using the provided context. If unsure, say you don't have that information."
)

# Minimum cosine similarity threshold to consider retrieved context relevant
MIN_RELEVANCE_THRESHOLD = 0.25

FALLBACK_GUARD_MESSAGE = (
    "I couldn't find any relevant opportunities or events in our database matching your request. "
    "Please try asking about available hackathons, internships, workshops, or competitions!"
)

# In-memory session store: session_id -> list of message dicts [{"role": ..., "content": ...}]
_SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}


# ── Session Management ────────────────────────────────────────────────────────

def get_session_history(session_id: str, limit_turns: int = 3) -> List[Dict[str, str]]:
    """Retrieves the last N turns (user + assistant pairs) of conversation history."""
    history = _SESSION_STORE.get(session_id, [])
    # 1 turn = 2 messages (user + assistant)
    max_messages = limit_turns * 2
    return history[-max_messages:]


def append_session_turn(session_id: str, user_message: str, assistant_response: str) -> None:
    """Appends a turn to the session history, capping at 20 messages."""
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = []
    _SESSION_STORE[session_id].append({"role": "user", "content": user_message})
    _SESSION_STORE[session_id].append({"role": "assistant", "content": assistant_response})
    # Keep store bounded
    if len(_SESSION_STORE[session_id]) > 20:
        _SESSION_STORE[session_id] = _SESSION_STORE[session_id][-20:]


def clear_session(session_id: str) -> None:
    """Clears history for a given session."""
    _SESSION_STORE.pop(session_id, None)


# ── RAG Grounding & Retrieval ─────────────────────────────────────────────────

async def retrieve_grounding_opportunities(
    query_text: str,
    top_k: int = 5,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Embeds the user query and retrieves top-k relevant opportunities/events from Supabase
    via pgvector cosine similarity.

    Returns:
      (matched_records, is_relevant)
    """
    embedder = get_embedder()
    query_vector = await embedder.embed(query_text)

    records: List[Dict[str, Any]] = []

    # 1. Try Supabase RPC match_opportunities (from V009)
    try:
        rpc_resp = supabase_admin.rpc(
            "match_opportunities",
            {
                "query_embedding": query_vector,
                "top_k": top_k,
                "min_score": 0.0,
            },
        ).execute()
        rpc_data = rpc_resp.data or []
        if rpc_data:
            records = rpc_data
    except Exception as rpc_exc:
        logger.debug(f"RPC match_opportunities not available ({rpc_exc}). Using table fetch fallback.")

    # 2. Table fetch + in-memory cosine fallback if RPC not available
    if not records:
        try:
            opps_resp = (
                supabase_admin.table("opportunities")
                .select("id, title, description, domain, type, location, organizer, deadline, eligibility, embedding")
                .eq("is_active", True)
                .execute()
            )
            opps = opps_resp.data or []
            scored = []
            for o in opps:
                emb = o.get("embedding")
                if emb:
                    sim = embedder.cosine_similarity(query_vector, emb)
                    sim = max(0.0, min(1.0, float(sim)))
                else:
                    sim = 0.1
                o["similarity"] = sim
                scored.append((sim, o))
            scored.sort(key=lambda x: x[0], reverse=True)
            records = [item[1] for item in scored[:top_k]]
        except Exception as exc:
            logger.warning(f"Failed to fetch opportunities for grounding: {exc}")
            return [], False

    if not records:
        return [], False

    # Check top match similarity against relevance threshold
    top_similarity = float(records[0].get("similarity", 0.0))
    if top_similarity < MIN_RELEVANCE_THRESHOLD:
        logger.info(f"Top match similarity ({top_similarity}) < {MIN_RELEVANCE_THRESHOLD}. Guard triggered.")
        return records, False

    # 3. Enrich opportunities with active event details
    opp_ids = [str(r["id"]) for r in records]
    try:
        events_resp = (
            supabase_admin.table("events")
            .select("id, opportunity_id, status, extra_details")
            .in_("opportunity_id", opp_ids)
            .execute()
        )
        events_by_opp: Dict[str, List[Dict[str, Any]]] = {}
        for ev in (events_resp.data or []):
            events_by_opp.setdefault(ev["opportunity_id"], []).append(ev)

        for r in records:
            r["events"] = events_by_opp.get(str(r["id"]), [])
    except Exception as exc:
        logger.debug(f"Could not enrich events for grounding ({exc}).")

    return records, True


# ── Prompt Builder & Ollama Dispatcher ────────────────────────────────────────

def build_copilot_prompt(
    user_message: str,
    retrieved_records: List[Dict[str, Any]],
    history: List[Dict[str, str]],
) -> str:
    """Constructs the prompt containing retrieved context, conversation history, and user question."""
    context_blocks = []
    for i, rec in enumerate(retrieved_records, 1):
        block = [
            f"[Opportunity {i}]",
            f"ID: {rec.get('id')}",
            f"Title: {rec.get('title', 'Unknown')}",
            f"Type: {rec.get('type', 'N/A')} | Domain: {rec.get('domain', 'N/A')}",
            f"Location: {rec.get('location', 'Online / Unspecified')}",
            f"Organizer: {rec.get('organizer', 'N/A')}",
            f"Deadline: {rec.get('deadline', 'Open')}",
            f"Description: {rec.get('description', 'No description provided.')}",
        ]
        if rec.get("eligibility"):
            block.append(f"Eligibility: {rec['eligibility']}")

        events = rec.get("events") or []
        if events:
            event_strs = []
            for ev in events:
                details = ev.get("extra_details") or {}
                event_strs.append(f"Status: {ev.get('status')} | Extra: {details}")
            block.append(f"Events: {'; '.join(event_strs)}")

        context_blocks.append("\n".join(block))

    context_str = "\n\n".join(context_blocks)

    history_str = ""
    if history:
        history_lines = []
        for msg in history:
            prefix = "Student:" if msg["role"] == "user" else "Copilot:"
            history_lines.append(f"{prefix} {msg['content']}")
        history_str = "\n".join(history_lines) + "\n\n"

    prompt = (
        f"CONTEXT INFORMATION:\n"
        f"---------------------\n"
        f"{context_str}\n"
        f"---------------------\n\n"
        f"{history_str}"
        f"Student: {user_message}\n\n"
        f"Copilot:"
    )
    return prompt


async def _generate_llm_response(prompt: str) -> str:
    """Executes prompt via active LLM provider (Gemini or Ollama) with graceful fallback."""
    from app.ml.llm_client import get_llm_client
    try:
        llm = await get_llm_client()
        return await llm.chat(
            user_prompt=prompt,
            system_prompt=SYSTEM_INSTRUCTIONS,
            temperature=0.2,
            max_tokens=400,
        )
    except Exception as exc:
        logger.warning(f"LLM call failed ({exc}). Using grounded fallback synthesizer.")
        return ""


def _synthesize_grounded_fallback(
    user_message: str,
    retrieved_records: List[Dict[str, Any]],
) -> str:
    """High-quality synthesis fallback grounded directly in retrieved opportunities."""
    lines = [
        f"Based on our opportunity database, here are the top matching opportunities for you:\n"
    ]
    for r in retrieved_records[:3]:
        title = r.get("title", "Opportunity")
        type_str = r.get("type", "opportunity").capitalize()
        loc = r.get("location", "Online")
        deadline = r.get("deadline", "Check listing")
        desc = r.get("description", "")[:120].strip() + "..."
        lines.append(f"• **{title}** ({type_str} | {loc}): {desc} (Deadline: {deadline})")

    lines.append(
        "\nFeel free to ask more details about eligibility, deadlines, or how to build a team for any of these!"
    )
    return "\n".join(lines)


# ── Core Copilot Chat Service ─────────────────────────────────────────────────

async def chat(request: CopilotChatRequest) -> CopilotChatResponse:
    """
    RAG conversational flow:
      1. Embed user query and retrieve top-5 relevant opportunities.
      2. Guard check: if retrieval finds nothing relevant, return safe fallback.
      3. Construct prompt with system instructions, retrieved context, and last 3 turns of history.
      4. Call local Ollama LLM to draft answer.
      5. Update session history and return answer with source citations.
    """
    clean_message = request.message.strip()
    if not clean_message:
        raise ValueError("Message cannot be empty.")

    # 1. Retrieve top-5 relevant opportunities from Supabase
    records, is_relevant = await retrieve_grounding_opportunities(clean_message, top_k=5)

    # 2. Guard Check: If retrieval returned nothing relevant, do not hallucinate
    if not is_relevant or not records:
        logger.info(f"Guard triggered for session {request.session_id}. Returning safe fallback.")
        append_session_turn(request.session_id, clean_message, FALLBACK_GUARD_MESSAGE)
        return CopilotChatResponse(
            session_id=request.session_id,
            answer=FALLBACK_GUARD_MESSAGE,
            source_opportunity_ids=[],
            sources=[],
            retrieval_guard_triggered=True,
        )

    # 3. Retrieve last 3 turns of conversation history
    history = get_session_history(request.session_id, limit_turns=3)

    # 4. Build prompt
    prompt = build_copilot_prompt(clean_message, records, history)

    # 5. Call active LLM (Gemini or Ollama based on app_settings)
    answer = await _generate_llm_response(prompt)
    if not answer:
        answer = _synthesize_grounded_fallback(clean_message, records)

    # 6. Save turn into session history
    append_session_turn(request.session_id, clean_message, answer)

    # 7. Format source citations
    citations: List[OpportunitySourceCitation] = []
    source_ids: List[UUID] = []

    for r in records:
        opp_id = UUID(str(r["id"]))
        source_ids.append(opp_id)
        citations.append(
            OpportunitySourceCitation(
                id=opp_id,
                title=r.get("title", ""),
                domain=r.get("domain"),
                type=r.get("type"),
                location=r.get("location"),
                deadline=str(r.get("deadline")) if r.get("deadline") else None,
                similarity=round(float(r.get("similarity", 0.0)), 4),
            )
        )

    return CopilotChatResponse(
        session_id=request.session_id,
        answer=answer,
        source_opportunity_ids=source_ids,
        sources=citations,
        retrieval_guard_triggered=False,
    )
