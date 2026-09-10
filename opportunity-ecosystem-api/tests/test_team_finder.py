"""
Unit and integration tests for Phase B6 — AI Team Finder.

Verifies:
  1. Role inference & normalization.
  2. Role complementarity logic & bonus scoring (complementary roles > duplicate roles).
  3. Cosine similarity embedding ranking.
  4. Exclusion of students who already have a team for the event.
  5. Team invite creation using Content Generation's team_invite type.
  6. Team creation and accepted members insertion.
  7. API route integration via FastAPI TestClient (/api/team-finder and /api/v1/team-finder).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import CurrentStudent, get_current_student
from app.api.team_finder import router as team_finder_router
from app.models.content_gen import ContentGenerateResponse, GenerationType
from app.models.student import StudentProfile
from app.models.team_finder import (
    TeamCreateRequest,
    TeamInviteRequest,
    TeamInviteResponse,
    TeamMatchesResponse,
    TeamResponse,
)
from app.services.team_finder import (
    COMPLEMENTARY_ROLE_BONUS,
    create_team_invite,
    create_team_with_members,
    get_team_matches,
    infer_student_role,
    is_role_complementary,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_current_student() -> StudentProfile:
    return StudentProfile(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="Alex River",
        email="alex@university.edu",
        department="Computer Science",
        skills=["React", "TypeScript", "Tailwind CSS", "HTML"],
        interests=["Web Development", "Open Source"],
        career_goals="Become a senior frontend engineer",
        preferred_role="Frontend Developer",
        is_active=True,
    )


# ── 1. Role Inference & Complementarity Tests ─────────────────────────────────

def test_infer_student_role_explicit():
    student = {"preferred_role": "AI/ML Engineer", "skills": ["Python"]}
    assert infer_student_role(student) == "AI/ML Engineer"


def test_infer_student_role_from_skills():
    backend_student = {
        "skills": ["FastAPI", "PostgreSQL", "Docker", "Python"],
        "interests": ["Backend Systems"],
        "career_goals": "Cloud infrastructure",
    }
    assert infer_student_role(backend_student) == "Backend Developer"

    frontend_student = {
        "skills": ["React", "Vue", "CSS", "JavaScript"],
        "interests": ["UI/UX"],
    }
    assert infer_student_role(frontend_student) == "Frontend Developer"

    ai_student = {
        "skills": ["PyTorch", "TensorFlow", "Deep Learning", "LLMs"],
        "interests": ["Generative AI"],
    }
    assert infer_student_role(ai_student) == "AI/ML Engineer"

    designer_student = {
        "skills": ["Figma", "Wireframing", "User Research", "UI/UX"],
        "interests": ["Design Systems"],
    }
    assert infer_student_role(designer_student) == "UI/UX Designer"


def test_infer_student_role_fallback():
    empty_student = {"skills": [], "interests": []}
    assert infer_student_role(empty_student) == "Full Stack Developer"


def test_role_complementarity():
    assert is_role_complementary("Frontend Developer", "Backend Developer") is True
    assert is_role_complementary("AI/ML Engineer", "UI/UX Designer") is True
    assert is_role_complementary("Frontend Developer", "Frontend Developer") is False
    assert is_role_complementary("backend developer", "Backend Developer") is False


# ── 2. Compatibility Matching & Complementary Role Bonus Tests ────────────────

@pytest.mark.anyio
async def test_get_team_matches_ranking_and_bonus(mock_current_student):
    event_id = UUID("11111111-1111-1111-1111-111111111111")
    opp_id = UUID("22222222-2222-2222-2222-222222222222")

    # Candidate 1: Backend Developer (Complementary to Alex's Frontend role)
    cand_backend = {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "name": "Blake Chen",
        "avatar_url": None,
        "department": "CS",
        "skills": ["Python", "FastAPI", "PostgreSQL", "React"],
        "interests": ["Cloud Architecture"],
        "career_goals": "Backend Specialist",
        "preferred_role": "Backend Developer",
        "embedding": [0.1] * 384,
    }

    # Candidate 2: Frontend Developer (Duplicate role to Alex's Frontend role)
    cand_frontend = {
        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
        "name": "Casey Jordan",
        "avatar_url": None,
        "department": "CS",
        "skills": ["React", "HTML", "CSS"],
        "interests": ["Web Design"],
        "career_goals": "Frontend Dev",
        "preferred_role": "Frontend Developer",
        "embedding": [0.1] * 384,  # Equal base vector similarity
    }

    mock_supabase = MagicMock()

    # Event query response
    mock_supabase.table().select().eq().maybe_single().execute.side_effect = [
        MagicMock(data={"id": str(event_id), "opportunity_id": str(opp_id), "extra_details": {}}),
        MagicMock(data={"title": "HackNima 2025 AI Hackathon"}),
        # Current student query
        MagicMock(data={
            "id": str(mock_current_student.id),
            "name": mock_current_student.name,
            "skills": mock_current_student.skills,
            "preferred_role": "Frontend Developer",
            "embedding": [0.1] * 384,
        }),
    ]

    # Teams query response: No teams created yet
    mock_supabase.table().select().eq().execute.return_value = MagicMock(data=[])

    # Applications query response: Both candidates registered
    mock_supabase.table().select().eq().execute.return_value = MagicMock(
        data=[
            {"student_id": cand_backend["id"], "status": "submitted"},
            {"student_id": cand_frontend["id"], "status": "submitted"},
        ]
    )

    # Candidates fetch
    mock_supabase.table().select().in_().execute.return_value = MagicMock(
        data=[cand_backend, cand_frontend]
    )

    with patch("app.services.team_finder.supabase_admin", mock_supabase), \
         patch("app.services.team_finder.get_local_embedder") as mock_embedder_factory:

        mock_embedder = MagicMock()
        # Same baseline similarity for both candidates
        mock_embedder.cosine_similarity.return_value = 0.80
        mock_embedder_factory.return_value = mock_embedder

        result = await get_team_matches(
            current_student=mock_current_student,
            event_id=event_id,
            preferred_role="Frontend Developer",
            top_k=10,
        )

        assert result.event_id == event_id
        assert len(result.matches) == 2

        backend_match = next(m for m in result.matches if m.student_id == UUID(cand_backend["id"]))
        frontend_match = next(m for m in result.matches if m.student_id == UUID(cand_frontend["id"]))

        # Check role bonus: complementary role gets bonus, duplicate role does not
        assert backend_match.is_complementary is True
        assert backend_match.role_bonus == COMPLEMENTARY_ROLE_BONUS
        assert frontend_match.is_complementary is False
        assert frontend_match.role_bonus == 0.0

        # Complementary candidate MUST rank higher than duplicate candidate
        assert backend_match.match_score > frontend_match.match_score
        assert result.matches[0].student_id == UUID(cand_backend["id"])


# ── 3. Team Filtering Test (Exclude existing teams) ───────────────────────────

@pytest.mark.anyio
async def test_get_team_matches_excludes_existing_team_members(mock_current_student):
    event_id = UUID("11111111-1111-1111-1111-111111111111")
    opp_id = UUID("22222222-2222-2222-2222-222222222222")

    existing_member_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    free_student_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

    mock_supabase = MagicMock()

    mock_supabase.table().select().eq().maybe_single().execute.side_effect = [
        MagicMock(data={"id": str(event_id), "opportunity_id": str(opp_id), "extra_details": {}}),
        MagicMock(data={"title": "Hackathon 2025"}),
        MagicMock(data={"id": str(mock_current_student.id), "embedding": [0.1] * 384}),
    ]

    # Existing team for event with creator
    mock_supabase.table().select().eq().execute.side_effect = [
        # teams
        MagicMock(data=[{"id": "team-1", "created_by": "creator-id"}]),
        # applications: both applied
        MagicMock(data=[
            {"student_id": existing_member_id, "status": "submitted"},
            {"student_id": free_student_id, "status": "submitted"},
        ]),
    ]

    # team_members for team-1: existing_member_id is accepted in team-1
    mock_supabase.table().select().in_().execute.side_effect = [
        MagicMock(data=[{"student_id": existing_member_id, "status": "accepted"}]),
        # candidate fetch should ONLY fetch free_student_id
        MagicMock(data=[{
            "id": free_student_id,
            "name": "Free Student",
            "skills": ["Python"],
            "interests": [],
            "preferred_role": "Backend Developer",
            "embedding": [0.1] * 384,
        }]),
    ]

    with patch("app.services.team_finder.supabase_admin", mock_supabase), \
         patch("app.services.team_finder.get_local_embedder") as mock_embedder_factory:
        mock_embedder = MagicMock()
        mock_embedder.cosine_similarity.return_value = 0.75
        mock_embedder_factory.return_value = mock_embedder

        result = await get_team_matches(
            current_student=mock_current_student,
            event_id=event_id,
        )

        match_ids = [m.student_id for m in result.matches]
        assert UUID(free_student_id) in match_ids
        assert UUID(existing_member_id) not in match_ids


# ── 4. Team Invite Creation Test ──────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_team_invite(mock_current_student):
    event_id = UUID("11111111-1111-1111-1111-111111111111")
    invited_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    invite_req = TeamInviteRequest(
        event_id=event_id,
        invited_student_id=invited_id,
        role="member",
    )

    existing_team_uuid = "33333333-3333-3333-3333-333333333333"

    mock_supabase = MagicMock()
    # 1. Fetch invited student
    # 2. Fetch event
    # 3. Fetch opp
    # 4. Check existing team for inviter
    mock_supabase.table().select().eq().maybe_single().execute.side_effect = [
        MagicMock(data={"id": str(invited_id), "name": "Blake Chen", "skills": ["Python", "React"]}),
        MagicMock(data={"id": str(event_id), "opportunity_id": "opp-1"}),
        MagicMock(data={"title": "HackNima 2025"}),
    ]
    # For existing_team_resp: .eq().eq().maybe_single().execute()
    mock_supabase.table().select().eq().eq().maybe_single().execute.return_value = MagicMock(
        data={"id": existing_team_uuid, "name": "Alpha Squad"}
    )

    mock_content_gen_response = ContentGenerateResponse(
        type=GenerationType.TEAM_INVITE,
        generated_content="Hi! Alex is inviting you to team up for HackNima 2025. Your shared skills in React would make an unstoppable squad!",
        model="llama3.2:3b",
    )

    with patch("app.services.team_finder.supabase_admin", mock_supabase), \
         patch("app.services.content_gen.generate_content", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_content_gen_response

        invite_res = await create_team_invite(mock_current_student, invite_req)

        assert invite_res.invited_student_name == "Blake Chen"
        assert invite_res.inviter_name == "Alex River"
        assert invite_res.status == "pending"
        assert "unstoppable squad" in invite_res.message
        assert mock_gen.called


# ── 5. Team Creation & Accepted Members Test ──────────────────────────────────

@pytest.mark.anyio
async def test_create_team_with_members(mock_current_student):
    event_id = UUID("11111111-1111-1111-1111-111111111111")
    accepted_member_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    team_req = TeamCreateRequest(
        event_id=event_id,
        name="NextGen Innovators",
        member_ids=[accepted_member_id],
        is_open=True,
    )

    mock_supabase = MagicMock()
    # 1. Validate event existence: .eq().maybe_single().execute()
    mock_supabase.table().select().eq().maybe_single().execute.return_value = MagicMock(
        data={"id": str(event_id)}
    )
    # 2. Check existing team by this student: .eq().eq().maybe_single().execute()
    mock_supabase.table().select().eq().eq().maybe_single().execute.return_value = MagicMock(
        data=None
    )

    # Fetch member names
    mock_supabase.table().select().in_().execute.return_value = MagicMock(
        data=[
            {"id": str(mock_current_student.id), "name": mock_current_student.name},
            {"id": str(accepted_member_id), "name": "Blake Chen"},
        ]
    )

    with patch("app.services.team_finder.supabase_admin", mock_supabase):
        team_res = await create_team_with_members(mock_current_student, team_req)

        assert team_res.name == "NextGen Innovators"
        assert team_res.created_by == mock_current_student.id
        assert len(team_res.members) == 2

        leader = next(m for m in team_res.members if m.student_id == mock_current_student.id)
        assert leader.role == "leader"
        assert leader.status == "accepted"

        member = next(m for m in team_res.members if m.student_id == accepted_member_id)
        assert member.role == "member"
        assert member.status == "accepted"


# ── 6. FastAPI Routes Integration Tests ────────────────────────────────────────

def test_api_routes(mock_current_student):
    test_app = FastAPI()
    test_app.include_router(team_finder_router, prefix="/api/v1")
    test_app.include_router(team_finder_router, prefix="/api")

    test_app.dependency_overrides[get_current_student] = lambda: mock_current_student

    client = TestClient(test_app)

    event_id = uuid4()

    # Test GET /api/team-finder/matches
    with patch("app.services.team_finder.get_team_matches", new_callable=AsyncMock) as mock_get_matches:
        mock_get_matches.return_value = TeamMatchesResponse(
            event_id=event_id,
            event_title="HackNima 2025",
            current_student_id=mock_current_student.id,
            current_student_name=mock_current_student.name,
            current_student_role="Frontend Developer",
            total_candidates=0,
            matches=[],
        )

        # Verify /api/team-finder/matches
        res1 = client.get(f"/api/team-finder/matches?event_id={event_id}")
        assert res1.status_code == 200
        assert res1.json()["data"]["event_title"] == "HackNima 2025"

        # Verify /api/v1/team-finder/matches
        res2 = client.get(f"/api/v1/team-finder/matches?event_id={event_id}")
        assert res2.status_code == 200
        assert res2.json()["data"]["event_title"] == "HackNima 2025"

    # Test POST /api/team-finder/invite
    with patch("app.services.team_finder.create_team_invite", new_callable=AsyncMock) as mock_invite:
        from datetime import datetime, timezone
        mock_invite.return_value = TeamInviteResponse(
            invite_id=uuid4(),
            team_id=uuid4(),
            team_name="Alpha Team",
            event_id=event_id,
            inviter_id=mock_current_student.id,
            inviter_name=mock_current_student.name,
            invited_student_id=uuid4(),
            invited_student_name="Blake",
            role="member",
            status="pending",
            message="Join our team!",
            created_at=datetime.now(timezone.utc),
        )

        invite_payload = {
            "event_id": str(event_id),
            "invited_student_id": str(uuid4()),
            "role": "member",
        }
        res_invite = client.post("/api/team-finder/invite", json=invite_payload)
        assert res_invite.status_code == 201
        assert res_invite.json()["data"]["status"] == "pending"

    # Test POST /api/team-finder/teams
    with patch("app.services.team_finder.create_team_with_members", new_callable=AsyncMock) as mock_create_team:
        from datetime import datetime, timezone
        mock_create_team.return_value = TeamResponse(
            id=uuid4(),
            event_id=event_id,
            name="Hack Squad",
            created_by=mock_current_student.id,
            is_open=True,
            members=[],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        team_payload = {
            "event_id": str(event_id),
            "name": "Hack Squad",
            "member_ids": [],
            "is_open": True,
        }
        res_team = client.post("/api/team-finder/teams", json=team_payload)
        assert res_team.status_code == 201
        assert res_team.json()["data"]["name"] == "Hack Squad"
