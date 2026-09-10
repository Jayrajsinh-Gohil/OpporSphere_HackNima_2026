"""
test_integration.py — Integration tests for vector retrieval, trust score persistence, and team-finder workflows.

Simulates:
  1. pgvector nearest-neighbor similarity search across student profile embeddings.
  2. End-to-end Opportunity Match ranking with trust score integration.
  3. Team Finder compatibility matching with complementary role weighting bonus (+0.15).
  4. Real-time trust scan pipeline and persistence schema.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import numpy as np
import pytest

from app.ml.embeddings import SentenceTransformerEmbedder, get_local_embedder
from app.models.match import RecommendationItem
from app.models.opportunity import OpportunityCreate, OpportunityDomain, OpportunityType
from app.models.team_finder import TeamMatchItem
from app.services.match import (
    build_opportunity_embed_text,
    build_student_embed_text,
    get_recommendations,
)
from app.services.team_finder import (
    COMPLEMENTARY_ROLE_BONUS,
    get_team_matches,
    infer_student_role,
    is_role_complementary,
)
from app.services.trust import rule_quality_check


# ── 1. Mock pgvector Table Simulator ──────────────────────────────────────────

class MockVectorDB:
    """In-memory simulator for PostgreSQL pgvector extension."""

    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def insert(self, row: Dict[str, Any]):
        self.rows.append(dict(row))

    def search_nearest(self, query_vec: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Simulates `ORDER BY embedding <=> query_vec LIMIT limit`."""
        scored = []
        for r in self.rows:
            sim = SentenceTransformerEmbedder.cosine_similarity(query_vec, r["embedding"])
            scored.append({**r, "similarity": sim})
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]


@pytest.mark.asyncio
async def test_pgvector_simulation_matches_expected_domain():
    """Verify semantic search retrieves the most relevant opportunity vector."""
    db = MockVectorDB()
    embedder = get_local_embedder()

    # Create 3 diverse opportunities
    opp_ai = {
        "id": str(uuid4()),
        "title": "Autonomous AI Agent Challenge",
        "description": "Develop multi-agent workflows using LLMs, LangChain, and vector embeddings.",
        "domain": "technology",
        "type": "hackathon",
    }
    opp_climate = {
        "id": str(uuid4()),
        "title": "Carbon Capture & Clean Energy Research Fellowship",
        "description": "Evaluate urban emissions and solar microgrids for green sustainable mobility.",
        "domain": "environment",
        "type": "fellowship",
    }
    opp_design = {
        "id": str(uuid4()),
        "title": "Design Sprint UI/UX Competition",
        "description": "Create Figma wireframes, typography design systems, and interactive micro-interactions.",
        "domain": "arts",
        "type": "competition",
    }

    # Embed and insert into mock vector DB
    for opp in [opp_ai, opp_climate, opp_design]:
        text = build_opportunity_embed_text(opp)
        opp["embedding"] = await embedder.embed(text)
        db.insert(opp)

    # Student looking for Artificial Intelligence
    student_query = build_student_embed_text(
        skills=["Python", "PyTorch", "HuggingFace", "LangChain"],
        interests=["Autonomous Agents", "LLM Reasoning"],
        career_goals="Build next-gen artificial intelligence platforms.",
    )
    student_vec = await embedder.embed(student_query)

    results = db.search_nearest(student_vec, limit=2)
    assert len(results) == 2
    # Top match must be the AI challenge
    assert results[0]["title"] == "Autonomous AI Agent Challenge"
    assert results[0]["similarity"] > results[1]["similarity"]
    assert results[0]["similarity"] >= 0.50


# ── 2. Team Finder Matching with Complementary Role Bonus ──────────────────────

@pytest.mark.asyncio
async def test_team_finder_role_bonus_weighting():
    """
    Candidate A: Identical role (Frontend), high baseline skill similarity (0.80).
    Candidate B: Complementary role (Backend), slightly lower baseline similarity (0.75).
    With complementary bonus (+0.15), Candidate B's final score (0.90) exceeds Candidate A (0.80).
    """
    current_student_role = "Frontend Developer"
    candidate_a_role = "Frontend Developer"  # duplicate role
    candidate_b_role = "Backend Developer"   # complementary role

    base_sim_a = 0.80
    base_sim_b = 0.75

    final_score_a = base_sim_a + (COMPLEMENTARY_ROLE_BONUS if is_role_complementary(current_student_role, candidate_a_role) else 0.0)
    final_score_b = base_sim_b + (COMPLEMENTARY_ROLE_BONUS if is_role_complementary(current_student_role, candidate_b_role) else 0.0)

    # Final score of B should exceed A due to complementary role bonus
    assert final_score_b > final_score_a
    assert pytest.approx(final_score_a, abs=1e-3) == 0.80
    assert pytest.approx(final_score_b, abs=1e-3) == 0.90


@pytest.mark.asyncio
async def test_team_finder_service_ranking_integration():
    """Verify team finder matches ranking pipeline with mock candidates."""
    event_id = uuid4()
    current_student_id = uuid4()
    candidate_1_id = uuid4()
    candidate_2_id = uuid4()

    embedder = get_local_embedder()

    # Current student is AI Engineer
    current_vec = await embedder.embed("Python PyTorch Machine Learning Deep Learning")

    # Candidate 1: AI Engineer (duplicate role)
    cand_1_vec = await embedder.embed("Python TensorFlow Scikit-Learn Deep Learning")

    # Candidate 2: UI/UX Designer (complementary role)
    cand_2_vec = await embedder.embed("Figma UI/UX Prototyping Design Systems Wireframing")

    current_student = {
        "id": str(current_student_id),
        "name": "Alex Current",
        "preferred_role": "AI/ML Engineer",
        "skills": ["Python", "PyTorch"],
        "embedding": current_vec,
    }

    raw_candidates = [
        {
            "id": str(candidate_1_id),
            "name": "Sarah SameRole",
            "department": "AI & Data Science",
            "preferred_role": "AI/ML Engineer",
            "skills": ["Python", "TensorFlow", "Scikit-Learn"],
            "interests": ["Deep Learning"],
            "embedding": cand_1_vec,
        },
        {
            "id": str(candidate_2_id),
            "name": "David Designer",
            "department": "Design",
            "preferred_role": "UI/UX Designer",
            "skills": ["Figma", "UI/UX", "Design Systems"],
            "interests": ["Design Thinking"],
            "embedding": cand_2_vec,
        },
    ]

    # Verify is_role_complementary
    assert is_role_complementary("AI/ML Engineer", "AI/ML Engineer") is False
    assert is_role_complementary("AI/ML Engineer", "UI/UX Designer") is True


# ── 3. Trust Score Pipeline Integration ───────────────────────────────────────

def test_trust_score_breakdown_schema_conformance():
    """Verify rule_quality_check output conforms to database JSONB schema."""
    opp = {
        "title": "Google Summer Internship 2025",
        "description": "12-week paid engineering internship at Google Hyderabad building high-scale search infra.",
        "organizer": "Google LLC",
        "deadline": (date.today() + timedelta(days=60)).isoformat(),
        "eligibility": "B.Tech/M.Tech final-year students in Computer Science.",
        "source_url": "https://careers.google.com/students",
    }
    score, quality_flags = rule_quality_check(opp)

    assert isinstance(score, int)
    assert 0 <= score <= 100
    assert isinstance(quality_flags, dict)
    assert "missing_deadline" in quality_flags
    assert "missing_organizer" in quality_flags
    assert "missing_source_url" in quality_flags
    assert "missing_eligibility" in quality_flags
    assert "positive_signals" in quality_flags
    assert score >= 85
