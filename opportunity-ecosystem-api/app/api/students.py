"""
Student routes — /api/v1/students

POST   /students/me   — create or fully update own profile
GET    /students/me   — read own profile
PATCH  /students/me   — partially update own profile
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentStudent
from app.models.base import APIResponse
from app.models.student import StudentCreate, StudentProfile, StudentUpdate
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


# ── GET /me ───────────────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=APIResponse[StudentProfile],
    summary="Read the authenticated student's profile",
)
async def get_my_profile(student: CurrentStudent):
    """
    Returns the profile of the currently authenticated student.
    The profile is looked up by the UUID in the Supabase JWT's `sub` claim.
    """
    return APIResponse(data=student)


# ── POST /me ──────────────────────────────────────────────────────────────────

@router.post(
    "/me",
    response_model=APIResponse[StudentProfile],
    status_code=status.HTTP_201_CREATED,
    summary="Create or fully replace own profile",
)
async def upsert_my_profile(
    body: StudentCreate,
    student: CurrentStudent,
):
    """
    Creates the profile if it doesn't exist, or fully replaces it.
    The `id` and `email` are always taken from the JWT — they cannot be
    supplied or overridden in the request body.
    """
    try:
        profile = await student_service.create_or_update_profile(
            student_id=student.id,
            email=student.email,
            data=body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return APIResponse(data=profile, message="Profile saved.")


# ── PATCH /me ─────────────────────────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=APIResponse[StudentProfile],
    summary="Partially update own profile",
)
async def patch_my_profile(
    body: StudentUpdate,
    student: CurrentStudent,
):
    """
    Updates only the fields supplied in the request body (PATCH semantics).
    Omitted fields are left unchanged.
    """
    try:
        profile = await student_service.update_profile(
            student_id=student.id,
            data=body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return APIResponse(data=profile, message="Profile updated.")
