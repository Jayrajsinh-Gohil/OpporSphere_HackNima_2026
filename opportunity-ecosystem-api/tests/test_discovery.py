"""
Unit and integration tests for Phase B7 — AI Smart Discovery.

Verifies:
  1. spaCy EntityRuler pattern extraction (domain, location, student type, opportunity type).
  2. Temporal constraint parsing ('this month', 'next week', 'in 2 weeks').
  3. Confidence score calculation (high confidence for structured queries vs low for freeform).
  4. Structured Supabase filter query execution (domain ILIKE, location ILIKE, deadline BETWEEN).
  5. pgvector semantic search fallback on low-confidence or 0 structured results.
  6. FastAPI route verification via TestClient (/api/discovery/search & /api/v1/discovery/search).
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.api.discovery import router as discovery_router
from app.models.discovery import (
    DiscoveredOpportunityItem,
    ExtractedFilters,
    SmartSearchResponse,
)
from app.services.discovery import (
    extract_search_entities,
    parse_time_constraint,
    smart_search,
)


# ── 1. Temporal Constraint Parser Tests ───────────────────────────────────────

def test_parse_time_constraint_this_month():
    ref = date(2025, 10, 5)
    start, end = parse_time_constraint("this month", ref_date=ref)
    assert start == date(2025, 10, 5)
    assert end == date(2025, 10, 31)


def test_parse_time_constraint_next_week():
    # 2025-10-06 is a Monday (weekday=0)
    ref = date(2025, 10, 6)
    start, end = parse_time_constraint("next week", ref_date=ref)
    assert start == date(2025, 10, 13)
    assert end == date(2025, 10, 19)


def test_parse_time_constraint_in_2_weeks():
    ref = date(2025, 10, 1)
    start, end = parse_time_constraint("in 2 weeks", ref_date=ref)
    assert start == date(2025, 10, 1)
    assert end == date(2025, 10, 15)


def test_parse_time_constraint_next_month():
    ref = date(2025, 10, 15)
    start, end = parse_time_constraint("next month", ref_date=ref)
    assert start == date(2025, 11, 1)
    assert end == date(2025, 11, 30)


# ── 2. Entity Extraction & Confidence Tests ───────────────────────────────────

def test_extract_search_entities_high_confidence():
    query = "AI hackathons in Bengaluru this month for computer science students"
    ref = date(2025, 11, 1)
    filters, confidence = extract_search_entities(query, ref_date=ref)

    assert filters.domain == "technology"
    assert filters.opportunity_type == "hackathon"
    assert filters.location is not None
    assert "Bengaluru" in filters.location or "bengaluru" in filters.location.lower()
    assert filters.department is not None
    assert filters.deadline_to == date(2025, 11, 30)
    assert confidence >= 0.7


def test_extract_search_entities_low_confidence():
    query = "something cool or fun to do"
    filters, confidence = extract_search_entities(query)

    assert filters.domain is None
    assert filters.location is None
    assert filters.deadline_to is None
    assert confidence < 0.5


# ── 3. Structured Filter Query Execution Tests ────────────────────────────────

@pytest.mark.anyio
async def test_smart_search_structured_filter_success():
    query = "AI hackathons in Bengaluru"
    opp_id = uuid4()

    mock_row = {
        "id": str(opp_id),
        "title": "HackNima 2025 AI Hackathon",
        "description": "48 hour AI hackathon",
        "domain": "technology",
        "type": "hackathon",
        "location": "Bengaluru, India",
        "organizer": "NimaTech",
        "deadline": "2025-11-15",
        "is_active": True,
    }

    mock_supabase = MagicMock()
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.ilike.return_value = chain
    chain.gte.return_value = chain
    chain.lte.return_value = chain
    chain.in_.return_value = chain
    chain.limit.return_value = chain
    chain.execute.side_effect = [
        MagicMock(data=[mock_row]),
        MagicMock(data=[{"opportunity_id": str(opp_id), "score": 88}]),
    ]
    mock_supabase.table.return_value = chain

    with patch("app.services.discovery.supabase_admin", mock_supabase):
        res = await smart_search(query, top_k=5)

        assert res.query == query
        assert res.search_mode == "structured_filter"
        assert res.confidence_score >= 0.5
        assert res.total == 1
        assert res.results[0].id == opp_id
        assert res.results[0].title == "HackNima 2025 AI Hackathon"
        assert res.results[0].trust_score == 88
        assert "technology" in res.results[0].match_reason.lower()


# ── 4. Semantic Search Fallback Tests ─────────────────────────────────────────

@pytest.mark.anyio
async def test_smart_search_semantic_fallback_on_low_confidence():
    query = "find exciting tech challenges for early career learners"
    opp_id = uuid4()

    mock_supabase = MagicMock()
    # RPC match_opportunities fails or returns fallback
    mock_supabase.rpc().execute.side_effect = Exception("RPC not found")

    # In-memory vector fetch
    mock_supabase.table().select().eq().execute.return_value = MagicMock(
        data=[
            {
                "id": str(opp_id),
                "title": "National Innovation Challenge",
                "description": "Challenge for learners",
                "domain": "technology",
                "type": "competition",
                "location": "Online",
                "organizer": "Ministry",
                "deadline": "2025-12-01",
                "embedding": [0.1] * 384,
            }
        ]
    )
    # Trust scores
    mock_supabase.table().select().in_().execute.return_value = MagicMock(
        data=[{"opportunity_id": str(opp_id), "score": 90}]
    )

    with patch("app.services.discovery.supabase_admin", mock_supabase), \
         patch("app.services.discovery.get_local_embedder") as mock_embedder_factory:
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 384)
        mock_embedder.cosine_similarity.return_value = 0.85
        mock_embedder_factory.return_value = mock_embedder

        res = await smart_search(query, top_k=5)

        assert res.query == query
        assert res.search_mode in ("semantic_fallback", "hybrid")
        assert res.total == 1
        assert res.results[0].id == opp_id
        assert res.results[0].relevance_score == 0.85
        assert "semantic match" in res.results[0].match_reason.lower()


# ── 5. FastAPI Endpoints Integration Tests ────────────────────────────────────

def test_api_discovery_search():
    test_app = FastAPI()
    test_app.include_router(discovery_router, prefix="/api/v1")
    test_app.include_router(discovery_router, prefix="/api")

    # Override auth claims dependency
    test_app.dependency_overrides[get_current_user] = lambda: {"sub": "test-user-id"}

    client = TestClient(test_app)

    opp_id = uuid4()
    mock_response = SmartSearchResponse(
        query="AI hackathons in Bengaluru",
        search_mode="structured_filter",
        confidence_score=0.85,
        filters_applied=ExtractedFilters(
            domain="technology",
            location="Bengaluru",
            opportunity_type="hackathon",
        ),
        total=1,
        results=[
            DiscoveredOpportunityItem(
                id=opp_id,
                title="HackNima 2025",
                description="AI Hackathon",
                domain="technology",
                type="hackathon",
                location="Bengaluru",
                trust_score=92,
                relevance_score=1.0,
                match_reason="Matched filters: domain technology, location Bengaluru",
            )
        ],
    )

    with patch("app.services.discovery.smart_search", new_callable=AsyncMock) as mock_smart_search:
        mock_smart_search.return_value = mock_response

        # Test POST /api/discovery/search
        resp1 = client.post("/api/discovery/search", json={"query": "AI hackathons in Bengaluru"})
        assert resp1.status_code == 200
        assert resp1.json()["data"]["search_mode"] == "structured_filter"
        assert resp1.json()["data"]["total"] == 1
        assert resp1.json()["data"]["results"][0]["title"] == "HackNima 2025"

        # Test POST /api/v1/discovery/search
        resp2 = client.post("/api/v1/discovery/search", json={"query": "AI hackathons in Bengaluru"})
        assert resp2.status_code == 200
        assert resp2.json()["data"]["search_mode"] == "structured_filter"
        assert resp2.json()["data"]["total"] == 1
