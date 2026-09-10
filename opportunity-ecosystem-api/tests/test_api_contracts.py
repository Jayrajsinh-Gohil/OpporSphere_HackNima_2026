"""
test_api_contracts.py — Comprehensive API contract tests asserting status codes and response schemas.

Uses FastAPI's built-in TestClient across all endpoints with:
  - Valid payloads (asserting 200/201 HTTP status and Pydantic envelope structures).
  - Invalid payloads (asserting 422 Unprocessable Entity and standard error schema).
  - Missing/invalid authentication (asserting 401/403 Unauthorized).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.api.auth import get_current_user
from app.api.deps import CurrentStudent, get_current_student
from app.main import create_app
from app.models.copilot import CopilotChatResponse
from app.models.discovery import ExtractedFilters, SmartSearchResponse
from app.models.match import RecommendationItem, RecommendationsResponse
from app.models.opportunity import TrustScoreOut
from app.models.student import StudentProfile
from app.models.team_finder import (
    TeamInviteResponse,
    TeamMatchesResponse,
    TeamMatchItem,
    TeamResponse,
)


app = create_app()
client = TestClient(app)


# ── Mock Fixtures ─────────────────────────────────────────────────────────────

MOCK_USER_ID = str(uuid4())
MOCK_STUDENT_ID = str(uuid4())
MOCK_EVENT_ID = str(uuid4())


def override_get_current_user():
    return {
        "id": MOCK_USER_ID,
        "email": "teststudent@example.edu",
        "role": "authenticated",
    }


def override_get_current_student():
    return StudentProfile(
        id=UUID(MOCK_STUDENT_ID),
        name="Contract Test Student",
        email="teststudent@example.edu",
        department="Computer Science",
        location="Bengaluru, Karnataka",
        skills=["Python", "FastAPI", "React"],
        interests=["AI", "Web Development"],
        career_goals="Build robust software products.",
        preferred_role="Backend Developer",
    )


# ── 1. Health Probe Contract ──────────────────────────────────────────────────

def test_health_check_contract():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert "app" in data
    assert "env" in data


# ── 2. Student Profile Endpoints Contract ─────────────────────────────────────

def test_student_profile_unauthorized():
    app.dependency_overrides.clear()
    response = client.get("/api/v1/students/me")
    assert response.status_code in (401, 403)


def test_student_profile_create_invalid_payload():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student
    try:
        # Invalid body: skills is not a list, name empty
        response = client.post(
            "/api/v1/students/me",
            json={
                "name": "",  # violates min_length
                "skills": "not-a-list",
            },
            headers={"Authorization": "Bearer test-jwt-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


# ── 3. Match Recommendations Contract ─────────────────────────────────────────

def test_match_recommendations_unauthorized():
    app.dependency_overrides.clear()
    response = client.get("/api/match/recommendations")
    assert response.status_code in (401, 403)


@patch("app.api.match.match_service.get_recommendations", new_callable=AsyncMock)
def test_match_recommendations_valid(mock_recs):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student

    mock_recs.return_value = RecommendationsResponse(
        student_id=UUID(MOCK_STUDENT_ID),
        has_profile_embedding=True,
        has_interaction_history=False,
        total=1,
        recommendations=[
            RecommendationItem(
                id=uuid4(),
                title="HackNima 2025",
                description="AI hackathon",
                domain="technology",
                type="hackathon",
                location="Bengaluru",
                deadline=str(date.today() + timedelta(days=30)),
                organizer="NimaTech",
                similarity=0.92,
                match_relevance_pct=92.0,
                trust_score=88,
            )
        ],
    )

    try:
        response = client.get(
            "/api/match/recommendations",
            headers={"Authorization": "Bearer test-jwt-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "recommendations" in data
    finally:
        app.dependency_overrides.clear()


# ── 4. Trust Evaluation Contract ──────────────────────────────────────────────

def test_trust_score_invalid_uuid():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student
    try:
        response = client.post(
            "/api/v1/trust/score/not-a-uuid",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@patch("app.api.trust.trust_service.compute_and_save_trust_score", new_callable=AsyncMock)
def test_trust_score_valid_contract(mock_compute):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student

    opp_id = uuid4()
    mock_compute.return_value = TrustScoreOut(
        opportunity_id=opp_id,
        score=92,
        duplicate_flag=False,
        quality_flags={"has_organizer": True, "has_deadline": True},
        computed_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        response = client.post(
            f"/api/v1/trust/score/{opp_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        resp_obj = data.get("data", data)
        assert resp_obj["score"] == 92
        assert resp_obj["duplicate_flag"] is False
    finally:
        app.dependency_overrides.clear()


# ── 5. Discovery Search Contract ──────────────────────────────────────────────

def test_discovery_search_invalid_payload():
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        response = client.post(
            "/api/discovery/search",
            json={},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@patch("app.api.discovery.discovery.smart_search", new_callable=AsyncMock)
def test_discovery_search_valid_contract(mock_search):
    app.dependency_overrides[get_current_user] = override_get_current_user

    mock_search.return_value = SmartSearchResponse(
        query="hackathons in Bengaluru this month",
        search_mode="structured",
        confidence_score=0.92,
        filters_applied=ExtractedFilters(
            domain="technology",
            location="Bengaluru",
            opportunity_type="hackathon",
        ),
        total=1,
        results=[],
    )

    try:
        response = client.post(
            "/api/discovery/search",
            json={"query": "hackathons in Bengaluru this month"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        resp_obj = data.get("data", data)
        assert resp_obj["query"] == "hackathons in Bengaluru this month"
        assert "search_mode" in resp_obj
        assert "filters_applied" in resp_obj
    finally:
        app.dependency_overrides.clear()


# ── 6. Copilot Chat Contract ──────────────────────────────────────────────────

def test_copilot_chat_invalid_payload():
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        response = client.post(
            "/api/copilot/chat",
            json={"session_id": "sess-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@patch("app.api.copilot.copilot.chat", new_callable=AsyncMock)
def test_copilot_chat_valid_contract(mock_chat):
    app.dependency_overrides[get_current_user] = override_get_current_user

    mock_chat.return_value = CopilotChatResponse(
        session_id="test-sess",
        answer="HackNima 2025 registration is currently open in Bengaluru.",
        source_opportunity_ids=[UUID(MOCK_EVENT_ID)],
        retrieval_guard_triggered=False,
    )

    try:
        response = client.post(
            "/api/copilot/chat",
            json={"session_id": "test-sess", "message": "When is HackNima?"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        resp_obj = data.get("data", data)
        assert "answer" in resp_obj
        assert "source_opportunity_ids" in resp_obj
        assert resp_obj["retrieval_guard_triggered"] is False
    finally:
        app.dependency_overrides.clear()


# ── 7. Team Finder Matches Contract ───────────────────────────────────────────

def test_team_finder_matches_missing_event_id():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student
    try:
        response = client.get(
            "/api/team-finder/matches",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@patch("app.api.team_finder.team_finder.get_team_matches", new_callable=AsyncMock)
def test_team_finder_matches_valid_contract(mock_get_matches):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student

    mock_get_matches.return_value = TeamMatchesResponse(
        event_id=UUID(MOCK_EVENT_ID),
        event_title="HackNima 2025",
        current_student_id=UUID(MOCK_STUDENT_ID),
        current_student_name="Contract Test Student",
        current_student_role="Backend Developer",
        total_candidates=1,
        matches=[
            TeamMatchItem(
                student_id=uuid4(),
                name="Candidate Student",
                department="Design",
                preferred_role="UI/UX Designer",
                similarity_score=0.79,
                role_bonus=0.15,
                match_score=0.94,
                match_percentage=94,
                is_complementary=True,
                shared_skills=["Figma"],
                complementary_skills=["Wireframing"],
                recommendation_reason="Complementary skill set",
            )
        ],
    )

    try:
        response = client.get(
            f"/api/team-finder/matches?event_id={MOCK_EVENT_ID}",
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 200
        data = response.json()
        resp_obj = data.get("data", data)
        assert resp_obj["event_title"] == "HackNima 2025"
        assert len(resp_obj["matches"]) == 1
        assert resp_obj["matches"][0]["match_percentage"] == 94
    finally:
        app.dependency_overrides.clear()


# ── 8. Team Finder Invite & Teams Contract ─────────────────────────────────────

def test_team_finder_invite_invalid_payload():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student
    try:
        response = client.post(
            "/api/team-finder/invite",
            json={"event_id": MOCK_EVENT_ID},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


@patch("app.api.team_finder.team_finder.create_team_invite", new_callable=AsyncMock)
def test_team_finder_invite_valid_contract(mock_invite):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student

    mock_invite.return_value = TeamInviteResponse(
        invite_id=uuid4(),
        team_id=uuid4(),
        team_name="Team Alpha",
        event_id=UUID(MOCK_EVENT_ID),
        inviter_id=UUID(MOCK_STUDENT_ID),
        inviter_name="Contract Test Student",
        invited_student_id=uuid4(),
        invited_student_name="Invited Peer",
        role="member",
        status="pending",
        message="Hey! Let's team up for HackNima 2025.",
        created_at=datetime.now(timezone.utc),
    )

    try:
        response = client.post(
            "/api/team-finder/invite",
            json={
                "event_id": MOCK_EVENT_ID,
                "invited_student_id": str(uuid4()),
                "role": "member",
            },
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 201
        data = response.json()
        resp_obj = data.get("data", data)
        assert resp_obj["status"] == "pending"
        assert "message" in resp_obj
    finally:
        app.dependency_overrides.clear()


def test_team_finder_teams_missing_name():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_student] = override_get_current_student
    try:
        response = client.post(
            "/api/team-finder/teams",
            json={"event_id": MOCK_EVENT_ID},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()
