"""
test_unit_services.py — Isolated unit tests for core services and algorithms.

Covers:
  1. Embedding generation shape (384 dimensions, float vectors, unit normalization).
  2. Cosine similarity calculation and ranking order.
  3. Trust score calculation edge cases:
     - Missing fields (deadline, eligibility, organizer, url).
     - Spam keyword detection.
     - Generic organizer penalties.
     - Perfect high-quality listing vs degraded listing.
  4. spaCy entity extraction and temporal parser on a fixed set of sample queries.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict
import numpy as np
import pytest

from app.ml.embeddings import SentenceTransformerEmbedder, get_local_embedder
from app.services.discovery import extract_search_entities, parse_time_constraint
from app.services.match import (
    build_opportunity_embed_text,
    build_student_embed_text,
)
from app.services.team_finder import (
    COMPLEMENTARY_ROLE_BONUS,
    infer_student_role,
    is_role_complementary,
)
from app.services.trust import GENERIC_ORGANIZERS, SPAM_KEYWORDS, rule_quality_check


# ── 1. Embedding Model Shape & Normalization Tests ────────────────────────────

@pytest.mark.asyncio
async def test_embedding_single_vector_shape_and_norm():
    """Verify single text embedding produces a 384-dim normalized vector."""
    embedder = get_local_embedder()
    text = "Full-stack web developer with experience in React, TypeScript, and FastAPI."
    vec = await embedder.embed(text)

    assert isinstance(vec, list), "Embedding should be a list of floats"
    assert len(vec) == 384, f"Expected 384 dimensions, got {len(vec)}"
    assert all(isinstance(x, float) for x in vec), "All elements must be floats"

    # Verify unit normalization (||v|| ≈ 1.0)
    norm = np.linalg.norm(vec)
    assert pytest.approx(norm, abs=1e-3) == 1.0, f"Vector norm {norm} should be ~1.0"


@pytest.mark.asyncio
async def test_embedding_batch_consistency():
    """Verify batch embedding preserves row count, dimension, and individual consistency."""
    embedder = get_local_embedder()
    texts = [
        "AI and machine learning enthusiast",
        "Cloud native infrastructure and Kubernetes DevOps engineer",
        "Product design and interactive prototyping using Figma",
    ]
    batch_vecs = await embedder.embed_batch(texts)

    assert len(batch_vecs) == len(texts)
    for vec in batch_vecs:
        assert len(vec) == 384
        assert pytest.approx(np.linalg.norm(vec), abs=1e-3) == 1.0

    # Single vs batch embedding of same text should match closely
    single_vec = await embedder.embed(texts[0])
    similarity = SentenceTransformerEmbedder.cosine_similarity(single_vec, batch_vecs[0])
    assert similarity >= 0.9999, f"Batch and single embedding should be identical, got {similarity}"


# ── 2. Cosine Similarity & Ranking Ordering Tests ─────────────────────────────

def test_cosine_similarity_identical_vectors():
    """Identical non-zero vectors should have similarity 1.0."""
    v = [0.1 * i for i in range(384)]
    sim = SentenceTransformerEmbedder.cosine_similarity(v, v)
    assert pytest.approx(sim, abs=1e-5) == 1.0


def test_cosine_similarity_orthogonal_vectors():
    """Orthogonal vectors should have similarity 0.0."""
    v1 = [1.0 if i == 0 else 0.0 for i in range(384)]
    v2 = [1.0 if i == 1 else 0.0 for i in range(384)]
    sim = SentenceTransformerEmbedder.cosine_similarity(v1, v2)
    assert pytest.approx(sim, abs=1e-5) == 0.0


def test_similarity_ranking_order():
    """Test ranking ordering sorts candidates strictly descending by similarity."""
    query = [1.0, 0.0, 0.0] + [0.0] * 381
    c1 = [0.9, 0.1, 0.0] + [0.0] * 381   # high similarity
    c2 = [0.2, 0.8, 0.0] + [0.0] * 381   # low similarity
    c3 = [0.6, 0.4, 0.0] + [0.0] * 381   # medium similarity

    candidates = [("c2", c2), ("c1", c1), ("c3", c3)]
    ranked = sorted(
        candidates,
        key=lambda x: SentenceTransformerEmbedder.cosine_similarity(query, x[1]),
        reverse=True,
    )

    ranked_ids = [x[0] for x in ranked]
    assert ranked_ids == ["c1", "c3", "c2"], f"Expected descending ranking, got {ranked_ids}"


# ── 3. Trust Score Calculation Edge Cases ─────────────────────────────────────

def test_trust_score_perfect_listing():
    """A complete listing with verifiable signals should achieve high score (>= 85)."""
    opp = {
        "title": "National Climate Action Hackathon 2025",
        "description": (
            "A comprehensive 48-hour challenge addressing environmental sustainability, "
            "carbon capture analytics, and renewable microgrids. Hardware kits provided for "
            "finalist teams, with mentorship by university professors and climate scientists."
        ),
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
        "eligibility": "Undergraduate students enrolled in recognized universities.",
        "organizer": "Ministry of Environment & Climate Innovation Fund",
        "source_url": "https://climatehack.gov.in/register",
    }
    score, flags = rule_quality_check(opp)

    assert score >= 85, f"Expected high score for complete listing, got {score}"
    assert flags["missing_deadline"] is False
    assert flags["missing_eligibility"] is False
    assert flags["missing_organizer"] is False
    assert flags["missing_source_url"] is False
    assert flags["generic_organizer"] is False
    assert flags["short_description"] is False
    assert flags["spam_keyword_detected"] is False
    assert len(flags["positive_signals"]) >= 3


def test_trust_score_missing_all_fields():
    """An opportunity missing organizer, deadline, eligibility, and URL receives heavy penalties."""
    opp = {
        "title": "Minimal Listing",
        "description": "Short description",
        "deadline": None,
        "eligibility": "",
        "organizer": "",
        "source_url": "",
    }
    score, flags = rule_quality_check(opp)

    assert flags["missing_deadline"] is True
    assert flags["missing_eligibility"] is True
    assert flags["missing_organizer"] is True
    assert flags["missing_source_url"] is True
    assert flags["short_description"] is True
    assert score <= 30, f"Expected heavily penalized score for empty listing, got {score}"


def test_trust_score_spam_keyword_detection():
    """Spam keywords such as '100% free money' or 'crypto airdrop' trigger severe penalties."""
    opp = {
        "title": "Guaranteed Prize 100% Free Money Event",
        "description": "Click here now for instant payout and crypto airdrop rewards. No work needed!",
        "deadline": (date.today() + timedelta(days=10)).isoformat(),
        "eligibility": "Open to everyone",
        "organizer": "Legit Team",
        "source_url": "https://legit-org.dev",
    }
    score, flags = rule_quality_check(opp)

    assert flags["spam_keyword_detected"] is True
    assert len(flags["detected_spam_phrases"]) >= 2
    assert score <= 60, f"Spam listing should be penalized under or equal to 60, got {score}"


def test_trust_score_generic_organizers():
    """Generic organizers like 'admin', 'test', 'anonymous' are penalized."""
    for generic in ["admin", "test", "anonymous", "unknown"]:
        opp = {
            "title": "Tech Challenge",
            "description": "A well written technical hackathon with valid details for students.",
            "deadline": (date.today() + timedelta(days=20)).isoformat(),
            "eligibility": "Engineering students",
            "organizer": generic,
            "source_url": "https://techchallenge.org",
        }
        score, flags = rule_quality_check(opp)
        assert flags["generic_organizer"] is True, f"Failed to flag generic organizer: {generic}"


# ── 4. Entity Extraction on Fixed Test Queries ────────────────────────────────

def test_extract_search_entities_tech_bengaluru():
    """Query: 'machine learning hackathon in Bengaluru this month'."""
    query = "machine learning hackathon in Bengaluru this month"
    filters, confidence = extract_search_entities(query)

    assert filters.domain in ["technology", "ai", "machine learning"] or "technology" in (filters.domain or "").lower()
    assert filters.opportunity_type == "hackathon"
    assert filters.location is not None and "bengaluru" in filters.location.lower()
    assert filters.deadline_from is not None or filters.deadline_to is not None
    assert confidence >= 0.75, f"Expected high confidence for structured query, got {confidence}"


def test_extract_search_entities_climate_delhi_undergraduate():
    """Query: 'climate change internships next week in Delhi for undergraduate students'."""
    query = "climate change internships next week in Delhi for undergraduate students"
    filters, confidence = extract_search_entities(query)

    assert filters.domain in ["environment", "climate"] or "environment" in (filters.domain or "").lower()
    assert filters.opportunity_type == "internship"
    assert filters.location is not None and "delhi" in filters.location.lower()
    assert filters.department is not None and "undergraduate" in filters.department.lower()
    assert filters.deadline_from is not None or filters.deadline_to is not None
    assert confidence >= 0.8


def test_extract_search_entities_vague_query():
    """Freeform vague query should yield low confidence for pgvector fallback."""
    query = "something cool to do soon with friends"
    filters, confidence = extract_search_entities(query)

    assert confidence < 0.6, f"Expected low confidence for vague query, got {confidence}"


# ── 5. Role Complementarity & Inference Tests ─────────────────────────────────

def test_infer_student_role_explicit_vs_inferred():
    """Infers roles accurately from explicit setting or skill keywords."""
    # Explicit role
    student_explicit = {"preferred_role": "AI/ML Engineer", "skills": ["Python"]}
    assert infer_student_role(student_explicit) == "AI/ML Engineer"

    # Inferred role: Frontend
    student_frontend = {
        "skills": ["React", "TypeScript", "Tailwind CSS", "Next.js"],
        "interests": ["UI/UX", "Interactive Web"],
        "career_goals": "Frontend Engineer",
    }
    assert infer_student_role(student_frontend) == "Frontend Developer"

    # Inferred role: Backend
    student_backend = {
        "skills": ["FastAPI", "PostgreSQL", "Docker", "Redis", "Kafka"],
        "interests": ["Microservices", "Databases"],
        "career_goals": "Backend Specialist",
    }
    assert infer_student_role(student_backend) == "Backend Developer"


def test_role_complementarity_bonus():
    """Complementary roles (Frontend + Backend) get bonus; duplicates get no bonus."""
    assert is_role_complementary("Frontend Developer", "Backend Developer") is True
    assert is_role_complementary("Frontend Developer", "Frontend Developer") is False
    assert is_role_complementary("AI/ML Engineer", "UI/UX Designer") is True
    assert COMPLEMENTARY_ROLE_BONUS > 0.0
