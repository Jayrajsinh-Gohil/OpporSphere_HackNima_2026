"""
Opportunity routes — /api/v1/opportunities

GET    /opportunities          — public, paginated list with filters
POST   /opportunities          — admin only: create new opportunity
GET    /opportunities/{id}     — public, single opportunity with trust signals
PATCH  /opportunities/{id}     — admin only: update opportunity
POST   /opportunities/{id}/events  — admin only: attach an event
GET    /opportunities/{id}/events  — public: list events for an opportunity
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import AdminStudent, CurrentStudent
from app.models.base import APIResponse, PaginationMeta
from app.models.opportunity import (
    EventCreate,
    EventOut,
    OpportunityCreate,
    OpportunityDomain,
    OpportunitySummary,
    OpportunityType,
    OpportunityUpdate,
)
from app.services import opportunity_service

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


# ── GET /opportunities ─────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=APIResponse[List[OpportunitySummary]],
    summary="List opportunities (public, paginated, filterable)",
)
async def list_opportunities(
    domain: Optional[OpportunityDomain] = Query(
        None, description="Filter by domain (e.g. technology, science)"
    ),
    type: Optional[OpportunityType] = Query(
        None, description="Filter by type (e.g. hackathon, internship)"
    ),
    location: Optional[str] = Query(
        None, description="Partial case-insensitive location filter"
    ),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Public endpoint — no authentication required.
    Returns active, non-duplicate opportunities ordered by trust score.
    """
    result = await opportunity_service.list_opportunities(
        domain=domain,
        type_=type,
        location=location,
        page=page,
        page_size=page_size,
    )
    return APIResponse(
        data=result["items"],
        pagination=PaginationMeta(
            page=result["page"],
            page_size=result["page_size"],
            total=result["total"],
            total_pages=result["total_pages"],
        ),
    )


# ── GET /opportunities/{id} ────────────────────────────────────────────────────

@router.get(
    "/{opportunity_id}",
    response_model=APIResponse[OpportunitySummary],
    summary="Get a single opportunity with trust signals (public)",
)
async def get_opportunity(opportunity_id: UUID):
    """Public endpoint — returns full opportunity detail plus trust score."""
    opp = await opportunity_service.get_opportunity(opportunity_id)
    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opportunity {opportunity_id} not found.",
        )
    return APIResponse(data=opp)


# ── POST /opportunities ────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=APIResponse[OpportunitySummary],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new opportunity (admin only)",
)
async def create_opportunity(
    body: OpportunityCreate,
    _admin: AdminStudent,           # enforces admin role; result unused
):
    """
    Admin-only endpoint.
    Creates the opportunity and immediately computes + stores its embedding.
    Configure admin emails in ADMIN_EMAILS in .env.
    """
    try:
        created = await opportunity_service.create_opportunity(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Fetch with trust signals from the view
    full = await opportunity_service.get_opportunity(created.id)
    return APIResponse(
        data=full or created,
        message="Opportunity created and embedding queued.",
    )


# ── PATCH /opportunities/{id} ─────────────────────────────────────────────────

@router.patch(
    "/{opportunity_id}",
    response_model=APIResponse[OpportunitySummary],
    summary="Partially update an opportunity (admin only)",
)
async def update_opportunity(
    opportunity_id: UUID,
    body: OpportunityUpdate,
    _admin: AdminStudent,
):
    """Admin-only. Re-embeds automatically if title/description/eligibility changed."""
    try:
        updated = await opportunity_service.update_opportunity(opportunity_id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    full = await opportunity_service.get_opportunity(opportunity_id)
    return APIResponse(data=full or updated, message="Opportunity updated.")


# ── Events sub-resource ────────────────────────────────────────────────────────

@router.post(
    "/{opportunity_id}/events",
    response_model=APIResponse[EventOut],
    status_code=status.HTTP_201_CREATED,
    summary="Add an event to an opportunity (admin only)",
)
async def create_event(
    opportunity_id: UUID,
    body: EventCreate,
    _admin: AdminStudent,
):
    """Create a new event (run/instance) for an opportunity."""
    # Ensure the opportunity_id in the path matches the body
    body.opportunity_id = opportunity_id
    try:
        event = await opportunity_service.create_event(body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return APIResponse(data=event, message="Event created.")


@router.get(
    "/{opportunity_id}/events",
    response_model=APIResponse[List[EventOut]],
    summary="List events for an opportunity (public)",
)
async def list_events(opportunity_id: UUID):
    """Returns all event instances for the given opportunity."""
    events = await opportunity_service.list_events(opportunity_id)
    return APIResponse(data=events)
