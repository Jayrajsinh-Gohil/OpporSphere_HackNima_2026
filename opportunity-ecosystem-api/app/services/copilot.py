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
    "You are Copilot, a friendly and helpful AI assistant for OpporSphere — a student opportunity platform. "
    "Your job is to help students discover hackathons, internships, fellowships, workshops, and competitions. "
    "When opportunity context is provided, base your answers on it and present details in a warm, conversational way. "
    "Always be encouraging and student-friendly. Never just list raw IDs or technical fields — speak like a helpful human advisor. "
    "For greetings and general questions not about specific opportunities, respond naturally and warmly. "
    "If you genuinely don't know something, say so honestly and suggest what the student can ask you."
)

# Minimum cosine similarity threshold to consider retrieved context relevant
MIN_RELEVANCE_THRESHOLD = 0.25

FALLBACK_GUARD_MESSAGE = (
    "I couldn't find any opportunities directly matching that query in our database right now. "
    "Try asking about hackathons, internships, workshops, research fellowships, or competitions — "
    "I can help you find the perfect opportunity! 🚀"
)

# Greeting/small-talk patterns — these bypass the RAG pipeline entirely
_GREETING_PATTERNS = [
    "hello", "hi", "hey", "howdy", "hiya", "good morning", "good afternoon",
    "good evening", "good night", "greetings", "sup", "what's up", "wassup",
    "thanks", "thank you", "thank u", "thx", "ty", "great", "awesome",
    "nice", "cool", "ok", "okay", "got it", "understood", "bye", "goodbye",
    "see you", "later", "how are you", "how r u", "how do you do",
    "who are you", "what are you", "what can you do", "help", "start",
]

_GREETING_RESPONSES = [
    (
        "👋 Hey there! I'm your OpporSphere Copilot — your personal guide to finding the best "
        "student opportunities! I can help you discover hackathons, internships, research fellowships, "
        "workshops, and competitions. \n\n"
        "Try asking me things like:\n"
        "• *What hackathons are available for CS students in India?*\n"
        "• *Are there any paid AI internships with open deadlines?*\n"
        "• *Which opportunities have cash prizes?*\n\n"
        "What are you looking for? 🚀"
    ),
    (
        "Hello! 😊 Great to have you here. I'm Copilot — think of me as your smart assistant "
        "for navigating student opportunities. Ask me about hackathons, internships, scholarships, "
        "or anything opportunity-related and I'll search our verified database for you!"
    ),
]


def _is_greeting_or_smalltalk(message: str) -> bool:
    """Returns True if the message is a simple greeting or small-talk phrase."""
    cleaned = message.lower().strip().rstrip("!?.")
    # Direct match
    if cleaned in _GREETING_PATTERNS:
        return True
    # Short messages that start with a greeting word
    words = cleaned.split()
    if len(words) <= 4 and words[0] in _GREETING_PATTERNS:
        return True
    return False


def _greeting_response(message: str) -> str:
    """Generate a contextual greeting response."""
    msg = message.lower()
    if any(w in msg for w in ["thanks", "thank", "thx", "ty"]):
        return (
            "You're welcome! 😊 Feel free to ask me anything about upcoming opportunities — "
            "hackathons, internships, fellowships, and more. I'm here to help!"
        )
    if any(w in msg for w in ["bye", "goodbye", "see you", "later"]):
        return (
            "Goodbye! 👋 Good luck with your applications — come back anytime to explore "
            "more opportunities on OpporSphere!"
        )
    if any(w in msg for w in ["who are you", "what are you", "what can you do", "help"]):
        return (
            "I'm **Copilot** — your AI assistant for finding student opportunities on OpporSphere! 🤖\n\n"
            "Here's what I can help you with:\n"
            "• 🏆 **Hackathons** — Find upcoming hack events by domain, location, or prize pool\n"
            "• 💼 **Internships** — Discover paid and research internship openings\n"
            "• 🎓 **Fellowships & Scholarships** — Explore funding opportunities\n"
            "• 🔬 **Workshops & Bootcamps** — Find skill-building events\n"
            "• ⏰ **Deadlines** — Get deadline reminders for any opportunity\n\n"
            "Just ask me anything in plain English!"
        )
    if any(w in msg for w in ["how are you", "how r u", "how do you do"]):
        return (
            "I'm doing great, thanks for asking! 😄 Ready to help you find amazing opportunities. "
            "What kind of opportunity are you looking for today?"
        )
    # Generic greeting
    import random
    return random.choice(_GREETING_RESPONSES)


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
    """Constructs a clean, conversational prompt with opportunity context."""
    context_blocks = []
    for i, rec in enumerate(retrieved_records, 1):
        title = rec.get('title', 'Unknown Opportunity')
        opp_type = str(rec.get('type', 'Opportunity')).capitalize()
        domain = rec.get('domain', 'Technology')
        location = rec.get('location', 'Online')
        organizer = rec.get('organizer', '')
        deadline = rec.get('deadline', 'Open / No deadline listed')
        description = rec.get('description', '')[:200].strip()
        eligibility = rec.get('eligibility', '')

        lines = [f"Opportunity {i}: {title}"]
        lines.append(f"  Type: {opp_type} | Domain: {domain}")
        if organizer:
            lines.append(f"  Organiser: {organizer}")
        lines.append(f"  Location: {location}")
        lines.append(f"  Application Deadline: {deadline}")
        if description:
            lines.append(f"  About: {description}")
        if eligibility:
            lines.append(f"  Eligibility: {eligibility}")

        events = rec.get("events") or []
        for ev in events[:2]:
            details = ev.get("extra_details") or {}
            ev_status = ev.get("status", "")
            if ev_status or details:
                ev_str = f"  Event Status: {ev_status}"
                if details.get("prize_pool"):
                    ev_str += f" | Prize Pool: {details['prize_pool']}"
                if details.get("max_team_size"):
                    ev_str += f" | Max Team Size: {details['max_team_size']}"
                if details.get("format"):
                    ev_str += f" | Format: {details['format']}"
                lines.append(ev_str)

        context_blocks.append("\n".join(lines))

    context_str = "\n\n".join(context_blocks)

    history_str = ""
    if history:
        history_lines = []
        for msg in history:
            prefix = "Student:" if msg["role"] == "user" else "Copilot:"
            history_lines.append(f"{prefix} {msg['content']}")
        history_str = "\n".join(history_lines) + "\n\n"

    prompt = (
        f"VERIFIED OPPORTUNITY DATABASE CONTEXT:\n"
        f"--------------------------------------\n"
        f"{context_str}\n"
        f"--------------------------------------\n\n"
        f"{history_str}"
        f"Student: {user_message}\n\n"
        f"Copilot (respond conversationally, be warm and helpful, highlight the most relevant opportunity "
        f"first, mention deadline and eligibility naturally — do NOT show raw IDs or technical field names):"
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
      0. Greeting / small-talk detection — bypass RAG for conversational messages.
      1. Embed user query and retrieve top-5 relevant opportunities.
      2. Guard check: if retrieval finds nothing relevant, return friendly fallback.
      3. Construct prompt with system instructions, retrieved context, and last 3 turns.
      4. Call active LLM (Gemini or Ollama) to generate response.
      5. Update session history and return answer with source citations.
    """
    clean_message = request.message.strip()
    if not clean_message:
        raise ValueError("Message cannot be empty.")

    # 0. Handle greetings and small-talk without hitting the RAG pipeline
    if _is_greeting_or_smalltalk(clean_message):
        reply = _greeting_response(clean_message)
        append_session_turn(request.session_id, clean_message, reply)
        return CopilotChatResponse(
            session_id=request.session_id,
            answer=reply,
            source_opportunity_ids=[],
            sources=[],
            retrieval_guard_triggered=False,
        )

    # 1. Retrieve top-5 relevant opportunities from Supabase
    records, is_relevant = await retrieve_grounding_opportunities(clean_message, top_k=5)

    # 2. Guard Check: If retrieval returned nothing relevant, return friendly fallback
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
