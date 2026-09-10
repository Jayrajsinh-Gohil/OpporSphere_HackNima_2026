"""
Team Finder routes — /api/v1/team-finder & /api/team-finder

Implements Phase B6:
  - GET  /api/team-finder/matches?event_id=X
  - POST /api/team-finder/invite
  - POST /api/team-finder/teams
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.auth import get_current_user
from app.api.deps import CurrentStudent
from app.models.base import APIResponse
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


# ── Phase B6: Teammate Matching ───────────────────────────────────────────────

@router.get(
    "/matches",
    response_model=APIResponse[TeamMatchesResponse],
    summary="Find compatible teammates for an event",
    description=(
        "For the logged-in student, finds other students registered for the specified event "
        "who do not already have a team. Ranks candidates by cosine similarity of skill/interest "
        "embeddings (reusing embeddings from Phase B3), and applies a bonus weight if "
        "preferred_role differs (complementary roles > duplicate roles)."
    ),
)
async def get_matches(
    current_student: CurrentStudent,
    event_id: UUID = Query(..., description="UUID of the event to find teammates for"),
    preferred_role: Optional[str] = Query(default=None, description="Optional role to evaluate complementarity against"),
    top_k: int = Query(default=10, ge=1, le=50, description="Max number of candidate matches to return"),
):
    try:
        matches_result = await team_finder.get_team_matches(
            current_student=current_student,
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
