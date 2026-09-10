"""
test_llm_outputs.py — Structural validation tests for non-deterministic generative outputs.

Verifies:
  1. Response is non-empty and trimmed.
  2. Response is bounded under reasonable character/token limits (< 4000 chars).
  3. Response does not leak internal prompt templates or system scaffolding:
     - "CONTEXT INFORMATION:"
     - "System:"
     - "Answer ONLY using the provided context"
     - "{context}"
  4. Response contains valid retrieved source citations matching database UUIDs.
  5. Hallucination guard triggers on low-similarity queries without hallucinating fake records.
"""

from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest

from app.models.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.copilot import (
    FALLBACK_GUARD_MESSAGE,
    SYSTEM_INSTRUCTIONS,
    _synthesize_grounded_fallback,
    build_copilot_prompt,
    chat,
    clear_session,
)


# ── Structural Output Property Tests ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_llm_output_structural_bounds_and_leak_guards():
    """Verify generative response satisfies length bounds and contains no leaked prompt scaffolding."""
    session_id = f"test-struct-{uuid4()}"
    clear_session(session_id)

    opp_id_1 = uuid4()
    opp_id_2 = uuid4()

    fake_records = [
        {
            "id": opp_id_1,
            "title": "HackNima 2025: AI For Social Good",
            "type": "hackathon",
            "domain": "technology",
            "location": "Bengaluru, Karnataka",
            "deadline": "2025-11-15",
            "description": "A premier 48-hour AI hackathon for Indian college students.",
            "organizer": "HackNima Foundation",
            "similarity": 0.88,
        },
        {
            "id": opp_id_2,
            "title": "Google Summer Internship 2025",
            "type": "internship",
            "domain": "technology",
            "location": "Hyderabad, Telangana",
            "deadline": "2025-12-01",
            "description": "12-week software engineering internship building search infrastructure.",
            "organizer": "Google India",
            "similarity": 0.82,
        },
    ]

    simulated_llm_answer = (
        "HackNima 2025 is scheduled for November 15, 2025 in Bengaluru, India. "
        "It is a 48-hour AI hackathon focused on social good. Additionally, "
        "Google's Summer Internship in Hyderabad has a deadline of December 1, 2025."
    )

    with patch("app.services.copilot.retrieve_grounding_opportunities", new_callable=AsyncMock) as mock_retrieval, \
         patch("app.services.copilot._generate_ollama_response", new_callable=AsyncMock) as mock_ollama:

        mock_retrieval.return_value = (fake_records, True)
        mock_ollama.return_value = simulated_llm_answer

        req = CopilotChatRequest(
            session_id=session_id,
            message="What are the upcoming AI hackathons and deadlines?",
        )
        response: CopilotChatResponse = await chat(req)

        # 1. Structural Property: Non-empty response
        assert response.answer is not None
        assert len(response.answer.strip()) > 10, "Response should be non-empty and descriptive"

        # 2. Structural Property: Max length bound (under 4000 characters)
        assert len(response.answer) < 4000, f"Response too long: {len(response.answer)} characters"

        # 3. Structural Property: Prompt template leak guard
        forbidden_phrases = [
            "CONTEXT INFORMATION:",
            "---------------------",
            "SYSTEM INSTRUCTIONS",
            "Answer ONLY using the provided context",
            "{context}",
            "{history}",
            "You are a helpful assistant for a student opportunity platform",
        ]
        for forbidden in forbidden_phrases:
            assert forbidden.lower() not in response.answer.lower(), (
                f"Security/Quality violation: Generative output leaked prompt template artifact: '{forbidden}'"
            )

        # 4. Structural Property: Source citations match retrieved records
        assert len(response.source_opportunity_ids) == 2
        assert response.source_opportunity_ids[0] == opp_id_1
        assert response.source_opportunity_ids[1] == opp_id_2
        assert response.retrieval_guard_triggered is False

    clear_session(session_id)


@pytest.mark.asyncio
async def test_llm_hallucination_guard_on_low_relevance():
    """Verify that queries with zero relevance trigger the fallback guard instead of hallucinating."""
    session_id = f"test-guard-{uuid4()}"
    clear_session(session_id)

    with patch("app.services.copilot.retrieve_grounding_opportunities", new_callable=AsyncMock) as mock_retrieval, \
         patch("app.services.copilot._generate_ollama_response", new_callable=AsyncMock) as mock_ollama:

        # Zero or sub-threshold relevance
        mock_retrieval.return_value = ([], False)

        req = CopilotChatRequest(
            session_id=session_id,
            message="How do I cook pasta carbonara at home?",
        )
        response: CopilotChatResponse = await chat(req)

        # Assert hallucination guard triggered
        assert response.retrieval_guard_triggered is True
        assert response.answer == FALLBACK_GUARD_MESSAGE
        assert response.source_opportunity_ids == []
        # Ollama LLM should not even be called when retrieval guard trips
        mock_ollama.assert_not_called()

    clear_session(session_id)


def test_synthesized_grounded_fallback_structural_properties():
    """Verify offline fallback synthesis returns clean structured markdown with citations."""
    fake_records = [
        {
            "id": uuid4(),
            "title": "ClimateTech Innovation Challenge",
            "type": "hackathon",
            "location": "New Delhi",
            "deadline": "2025-10-30",
            "description": "Build IoT soil sensors and solar microgrid controllers for farmers.",
        }
    ]

    fallback = _synthesize_grounded_fallback("climate hackathon", fake_records)

    assert "ClimateTech Innovation Challenge" in fallback
    assert "2025-10-30" in fallback
    assert len(fallback) < 2000
    assert "CONTEXT INFORMATION" not in fallback
