"""
Unit and integration tests for Phase B8 — AI Student Copilot (RAG).

Verifies:
  1. Multi-turn session history management (last 3 turns / 6 messages).
  2. pgvector retrieval and live opportunity/event context grounding.
  3. Hallucination guard: low-relevance queries trigger fallback without LLM invocation.
  4. Prompt construction with system instructions, context blocks, and conversation history.
  5. Source opportunity IDs returned for UI citation.
  6. FastAPI route verification via TestClient (/api/copilot/chat & /api/v1/copilot/chat).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.api.copilot import router as copilot_router
from app.models.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    OpportunitySourceCitation,
)
from app.services.copilot import (
    FALLBACK_GUARD_MESSAGE,
    SYSTEM_INSTRUCTIONS,
    append_session_turn,
    build_copilot_prompt,
    chat,
    clear_session,
    get_session_history,
    retrieve_grounding_opportunities,
)


# ── 1. Session History Tests ──────────────────────────────────────────────────

def test_session_history_turn_limiting():
    session_id = f"test-sess-{uuid4()}"
    clear_session(session_id)

    # Add 5 turns (10 messages)
    for i in range(1, 6):
        append_session_turn(session_id, f"User question {i}", f"Assistant answer {i}")

    # Request last 3 turns
    history = get_session_history(session_id, limit_turns=3)
    assert len(history) == 6  # 3 turns = 6 messages

    # Verify order is most recent 3 turns (turns 3, 4, 5)
    assert history[0]["content"] == "User question 3"
    assert history[1]["content"] == "Assistant answer 3"
    assert history[-2]["content"] == "User question 5"
    assert history[-1]["content"] == "Assistant answer 5"

    clear_session(session_id)


# ── 2. Prompt Builder Tests ───────────────────────────────────────────────────

def test_build_copilot_prompt():
    records = [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "title": "HackNima 2025 AI Hackathon",
            "type": "hackathon",
            "domain": "technology",
            "location": "Bengaluru",
            "organizer": "NimaTech",
            "deadline": "2025-11-15",
            "description": "48 hour social impact hackathon.",
            "eligibility": "Open to all enrolled university students.",
        }
    ]
    history = [
        {"role": "user", "content": "What events are happening soon?"},
        {"role": "assistant", "content": "We have several hackathons coming up."},
    ]

    prompt = build_copilot_prompt("Can I apply to HackNima?", records, history)

    assert "CONTEXT INFORMATION" in prompt
    assert "HackNima 2025 AI Hackathon" in prompt
    assert "11111111-1111-1111-1111-111111111111" in prompt
    assert "Student: What events are happening soon?" in prompt
    assert "Copilot: We have several hackathons coming up." in prompt
    assert "Student: Can I apply to HackNima?" in prompt


# ── 3. Hallucination Guard Tests ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_retrieval_guard_triggered_on_low_similarity():
    session_id = f"test-sess-guard-{uuid4()}"
    clear_session(session_id)

    mock_supabase = MagicMock()
    # Mock RPC returning low similarity results (< 0.25 threshold)
    mock_supabase.rpc().execute.return_value = MagicMock(
        data=[
            {
                "id": str(uuid4()),
                "title": "Unrelated Art Class",
                "similarity": 0.12,
            }
        ]
    )

    with patch("app.services.copilot.supabase_admin", mock_supabase), \
         patch("app.services.copilot.get_local_embedder") as mock_embedder_factory:
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 384)
        mock_embedder_factory.return_value = mock_embedder

        req = CopilotChatRequest(
            session_id=session_id,
            message="How do I bake sourdough bread?",
        )
        resp = await chat(req)

        assert resp.retrieval_guard_triggered is True
        assert resp.answer == FALLBACK_GUARD_MESSAGE
        assert resp.source_opportunity_ids == []
        assert resp.sources == []

    clear_session(session_id)


# ── 4. Grounded RAG Chat Flow with Citations Tests ───────────────────────────

@pytest.mark.anyio
async def test_copilot_chat_successful_rag_with_citations():
    session_id = f"test-sess-rag-{uuid4()}"
    clear_session(session_id)

    opp_id = UUID("11111111-1111-1111-1111-111111111111")
    record = {
        "id": str(opp_id),
        "title": "Google Summer Internship 2025",
        "description": "12-week paid software engineering summer internship.",
        "domain": "technology",
        "type": "internship",
        "location": "Hyderabad, India",
        "organizer": "Google LLC",
        "deadline": "2025-12-01",
        "eligibility": "Final-year CS students.",
        "similarity": 0.88,
    }

    mock_supabase = MagicMock()
    # RPC match_opportunities
    mock_supabase.rpc().execute.return_value = MagicMock(data=[record])
    # Events enrichment
    mock_supabase.table().select().in_().execute.return_value = MagicMock(data=[])

    with patch("app.services.copilot.supabase_admin", mock_supabase), \
         patch("app.services.copilot.get_local_embedder") as mock_embedder_factory, \
         patch("app.services.copilot._generate_ollama_response", new_callable=AsyncMock) as mock_ollama:

        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 384)
        mock_embedder_factory.return_value = mock_embedder

        mock_ollama.return_value = (
            "The Google Summer Internship 2025 is located in Hyderabad, India, "
            "with a deadline on December 1, 2025. It is open to final-year CS students."
        )

        req = CopilotChatRequest(
            session_id=session_id,
            message="Tell me about the Google internship deadline and location",
        )
        resp = await chat(req)

        assert resp.retrieval_guard_triggered is False
        assert "Google Summer Internship" in resp.answer
        assert "December 1, 2025" in resp.answer
        assert opp_id in resp.source_opportunity_ids
        assert len(resp.sources) == 1
        assert resp.sources[0].id == opp_id
        assert resp.sources[0].title == "Google Summer Internship 2025"

        # Check session history was updated
        history = get_session_history(session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    clear_session(session_id)


# ── 5. FastAPI Endpoints Integration Tests ────────────────────────────────────

def test_api_copilot_chat():
    test_app = FastAPI()
    test_app.include_router(copilot_router, prefix="/api/v1")
    test_app.include_router(copilot_router, prefix="/api")

    test_app.dependency_overrides[get_current_user] = lambda: {"sub": "user-123"}

    client = TestClient(test_app)

    opp_id = uuid4()
    mock_response = CopilotChatResponse(
        session_id="sess-abc",
        answer="HackNima 2025 is a 48-hour AI hackathon in Bengaluru.",
        source_opportunity_ids=[opp_id],
        sources=[
            OpportunitySourceCitation(
                id=opp_id,
                title="HackNima 2025",
                domain="technology",
                type="hackathon",
                location="Bengaluru",
                similarity=0.91,
            )
        ],
        retrieval_guard_triggered=False,
    )

    with patch("app.services.copilot.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = mock_response

        # Test POST /api/copilot/chat
        resp1 = client.post(
            "/api/copilot/chat",
            json={"session_id": "sess-abc", "message": "Where is HackNima hosted?"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["data"]["answer"] == "HackNima 2025 is a 48-hour AI hackathon in Bengaluru."
        assert str(opp_id) in [str(s) for s in resp1.json()["data"]["source_opportunity_ids"]]

        # Test POST /api/v1/copilot/chat
        resp2 = client.post(
            "/api/v1/copilot/chat",
            json={"session_id": "sess-abc", "message": "Where is HackNima hosted?"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["data"]["answer"] == "HackNima 2025 is a 48-hour AI hackathon in Bengaluru."
