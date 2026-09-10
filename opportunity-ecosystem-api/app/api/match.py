from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentStudent
from app.models.base import APIResponse
from app.models.match import (
    MatchRequest,
    MatchResponse,
    OpportunityCreate,
    RecommendationsResponse,
)
from app.services import match_service

router = APIRouter(prefix="/match", tags=["Match"])


@router.get(
    "/recommendations",
    response_model=APIResponse[RecommendationsResponse],
    summary="Get AI opportunity recommendations for the logged-in student",
    description=(
        "Performs a pgvector cosine similarity search against the student's profile embedding. "
        "Returns a ranked list of opportunities with 'match relevance %'. "
        "Includes cold-start and interaction history fallbacks."
    ),
)
async def get_student_recommendations(
    current_student: CurrentStudent,
    top_k: int = Query(default=10, ge=1, le=50, description="Max recommendations to return"),
    min_score: float = Query(default=0.0, ge=0.0, le=1.0, description="Minimum similarity threshold"),
):
    try:
        recommendations = await match_service.get_recommendations(
            student_id=current_student.id,
            top_k=top_k,
            min_score=min_score,
        )
        return APIResponse(data=recommendations)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {exc}",
        )


@router.post(
    "/",
    response_model=APIResponse[MatchResponse],
    summary="Match a user to the best opportunities",
)
async def match(
    body: MatchRequest,
    current_student: CurrentStudent,
):
    try:
        result = await match_service.match_opportunities(body)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    return APIResponse(data=result)


@router.post(
    "/opportunities",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new opportunity and embed its text",
)
async def create_opportunity(
    body: OpportunityCreate,
    current_student: CurrentStudent,
):
    from app.core.supabase_client import supabase_admin
    from uuid import uuid4

    new_id = str(uuid4())
    row = body.model_dump()
    row["id"] = new_id

    resp = supabase_admin.table("opportunities").insert(row).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create opportunity.")

    # Embed via sentence-transformers pipeline
    from uuid import UUID
    await match_service.embed_and_store_opportunity(UUID(new_id), body.model_dump())

    return APIResponse(data=resp.data[0], message="Opportunity created and embedded.")
