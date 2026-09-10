"""
Team Finder routes — /api/v1/team-finder & /api/team-finder

Implements Phase B6:
  - GET  /api/team-finder/matches?event_id=X
  - POST /api/team-finder/invite
  - POST /api/team-finder/teams
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger

from app.api.auth import get_current_user
from app.api.deps import CurrentStudent, OptionalStudent
from app.core.supabase_client import supabase_admin
from app.models.base import APIResponse
from app.models.student import StudentProfile
from app.models.team_finder import (
    TeamCreateRequest,
    TeamFinderRequest,
    TeamFinderResponse,
    TeamInviteRequest,
    TeamInviteResponse,
    TeamMatchesResponse,
    TeamResponse,
)
from app.services import team_finder, team_finder_service

router = APIRouter(prefix="/team-finder", tags=["Team Finder"])


# ── Active Events for Team Finder ─────────────────────────────────────────────

@router.get(
    "/events",
    response_model=APIResponse[List[Dict[str, Any]]],
    summary="Get active events for team matching (public)",
)
async def get_team_finder_events():
    """Returns active hackathons and competition events from the database for team formation."""
    try:
        resp = (
            supabase_admin.table("events")
            .select("id, opportunity_id, status, registration_link, extra_details, opportunities(id, title, domain, type, location, organizer, deadline)")
            .execute()
        )
        data = resp.data or []

        formatted = []
        for ev in data:
            opp = ev.get("opportunities") or {}
            extra = ev.get("extra_details") or {}
            formatted.append({
                "id": ev["id"],
                "opportunity_id": ev.get("opportunity_id"),
                "title": opp.get("title") or "Hackathon Event",
                "domain": opp.get("domain") or "technology",
                "type": opp.get("type") or "hackathon",
                "location": opp.get("location") or "India",
                "organizer": opp.get("organizer") or "Organizer",
                "deadline": opp.get("deadline") or "Open",
                "date": f"Deadline: {opp.get('deadline') or 'Upcoming'}",
                "status": ev.get("status") or "open",
                "prize_pool": extra.get("prize_pool") or "Prizes & Recognition",
                "max_team_size": extra.get("max_team_size") or 4,
                "format": extra.get("format") or "Hybrid",
            })
        return APIResponse(data=formatted, message=f"Loaded {len(formatted)} events.")
    except Exception as exc:
        logger.error(f"Error fetching team finder events: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Student Candidates Across India ──────────────────────────────────────────

@router.get(
    "/candidates",
    response_model=APIResponse[List[Dict[str, Any]]],
    summary="List student candidates across India (public)",
)
async def get_candidates(
    limit: int = Query(default=50, ge=1, le=100),
    role: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
):
    """Returns real student builders across India with their skills and interests."""
    try:
        query = (
            supabase_admin.table("students")
            .select("id, name, email, department, location, skills, interests, career_goals, avatar_url")
            .eq("is_active", True)
        )
        if location:
            query = query.ilike("location", f"%{location}%")
        resp = query.limit(limit).execute()
        students = resp.data or []
        results = []
        for s in students:
            inferred_role = team_finder.infer_student_role(s)
            if role and role.lower() not in inferred_role.lower():
                continue
            results.append({
                "student_id": s["id"],
                "name": s["name"],
                "department": s.get("department") or "Engineering",
                "location": s.get("location") or "India",
                "preferred_role": inferred_role,
                "skills": s.get("skills") or [],
                "interests": s.get("interests") or [],
                "career_goals": s.get("career_goals") or "",
                "avatar_url": s.get("avatar_url"),
            })
        return APIResponse(data=results, message=f"Retrieved {len(results)} student candidates.")
    except Exception as exc:
        logger.error(f"Error fetching candidates: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ── Phase B6: Teammate Matching ───────────────────────────────────────────────

@router.get(
    "/matches",
    response_model=APIResponse[TeamMatchesResponse],
    summary="Find compatible teammates for an event",
    description=(
        "Finds students registered for the specified event who do not already have a team. "
        "Ranks candidates by cosine similarity of skill/interest embeddings and applies a bonus weight "
        "if preferred_role differs (complementary roles > duplicate roles)."
    ),
)
async def get_matches(
    event_id: UUID = Query(..., description="UUID of the event to find teammates for"),
    current_student: OptionalStudent = None,
    preferred_role: Optional[str] = Query(default=None, description="Optional role to evaluate complementarity against"),
    top_k: int = Query(default=20, ge=1, le=50, description="Max number of candidate matches to return"),
):
    try:
        # If unauthenticated visitor, select a representative student profile as perspective
        active_student = current_student
        if not active_student:
            first_s = (
                supabase_admin.table("students")
                .select("id, name, email, department, location, skills, interests, career_goals")
                .limit(1)
                .execute()
            )
            if first_s.data:
                active_student = StudentProfile(**first_s.data[0])
            else:
                from uuid import uuid4
                active_student = StudentProfile(
                    id=uuid4(),
                    name="Student Explorer",
                    email="student@opporsphere.edu",
                    department="Computer Science",
                    skills=["Python", "Web Development", "AI/ML"],
                    interests=["Hackathons", "Open Source"],
                )

        matches_result = await team_finder.get_team_matches(
            current_student=active_student,
            event_id=event_id,
            preferred_role=preferred_role,
            top_k=top_k,
        )
        return APIResponse(
            data=matches_result,
            message=f"Found {len(matches_result.matches)} potential teammates for {matches_result.event_title}.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error(f"Error finding team matches: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find team matches: {exc}",
        )


# ── Phase B6: Team Invite ─────────────────────────────────────────────────────

@router.post(
    "/invite",
    response_model=APIResponse[TeamInviteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Invite a student to join a team",
    description=(
        "Creates a pending team_members invite row. "
        "Uses Content Generation's team_invite type to automatically draft a "
        "personalized, enthusiastic invite message based on shared skills."
    ),
)
async def send_team_invite(
    body: TeamInviteRequest,
    current_student: CurrentStudent,
):
    try:
        invite_result = await team_finder.create_team_invite(
            current_student=current_student,
            request=body,
        )
        return APIResponse(
            data=invite_result,
            message=f"Invite sent to {invite_result.invited_student_name} successfully.",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team invite: {exc}",
        )


# ── Phase B6: Team Creation ───────────────────────────────────────────────────

@router.post(
    "/teams",
    response_model=APIResponse[TeamResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a team and add accepted members",
    description=(
        "Creates a team for a specific event. The logged-in student is assigned as "
        "the team leader. Any student IDs specified in member_ids are added as accepted members."
    ),
)
async def create_team(
    body: TeamCreateRequest,
    current_student: CurrentStudent,
):
    try:
        team_result = await team_finder.create_team_with_members(
            current_student=current_student,
            request=body,
        )
        return APIResponse(
            data=team_result,
            message=f"Team '{team_result.name}' created successfully with {len(team_result.members)} member(s).",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create team: {exc}",
        )


# ── Legacy Endpoint Compatibility ─────────────────────────────────────────────

@router.post(
    "/",
    response_model=APIResponse[TeamFinderResponse],
    summary="Suggest a team for an opportunity (legacy)",
)
async def find_team(
    body: TeamFinderRequest,
    _claims: dict = Depends(get_current_user),
):
    try:
        result = await team_finder_service.find_team(body)
        return APIResponse(data=result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
