"""
Trust routes — /api/v1/trust
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentStudent
from app.models.base import APIResponse
from app.models.opportunity import TrustScoreOut
from app.models.trust import EndorsementCreate, RatingCreate, TrustScore
from app.services import trust_service

router = APIRouter(prefix="/trust", tags=["Trust"])


@router.post(
    "/score/{opportunity_id}",
    response_model=APIResponse[TrustScoreOut],
    summary="Compute and store trust & duplicate score for an opportunity",
    description="Runs duplicate detection (cosine > 0.92 + RapidFuzz) and quality scoring (rules + LogisticRegression classifier), saving results to the trust_scores table.",
)
async def score_opportunity(
    opportunity_id: UUID,
    current_student: CurrentStudent,
):
    try:
        result = await trust_service.compute_and_save_trust_score(opportunity_id)
        return APIResponse(data=result, message="Trust score computed and stored successfully.")
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute trust score: {exc}",
        )


@router.get(
    "/score/{opportunity_id}",
    response_model=APIResponse[TrustScoreOut],
    summary="Get trust & duplicate score for an opportunity",
)
async def get_opportunity_score(
    opportunity_id: UUID,
    current_student: CurrentStudent,
):
    result = await trust_service.get_opportunity_trust_score(opportunity_id)
    return APIResponse(data=result)


@router.get(
    "/{user_id}",
    response_model=APIResponse[TrustScore],
    summary="Get trust score for a user",
)
async def get_trust(
    user_id: UUID,
    current_student: CurrentStudent,
):
    score = await trust_service.get_trust_score(user_id)
    return APIResponse(data=score)


@router.post(
    "/endorse",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Endorse a peer for a skill",
)
async def endorse(
    body: EndorsementCreate,
    current_student: CurrentStudent,
):
    endorser_id = current_student.id
    if endorser_id == body.endorsed_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot endorse yourself.",
        )
    result = await trust_service.add_endorsement(endorser_id, body)
    return APIResponse(data=result, message="Endorsement recorded.")


@router.post(
    "/rate",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Rate a peer after a shared opportunity",
)
async def rate(
    body: RatingCreate,
    current_student: CurrentStudent,
):
    rater_id = current_student.id
    if rater_id == body.rated_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot rate yourself.",
        )
    result = await trust_service.add_rating(rater_id, body)
    return APIResponse(data=result, message="Rating submitted.")
