"""
Trust service — compute and manage user reputation scores.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.models.opportunity import TrustScoreOut
from app.models.trust import EndorsementCreate, RatingCreate, TrustScore
from app.services.trust import compute_and_save_trust_score


async def get_opportunity_trust_score(opportunity_id: UUID) -> TrustScoreOut:
    """Fetch or compute trust score for an opportunity."""
    resp = (
        supabase_admin.table("trust_scores")
        .select("*")
        .eq("opportunity_id", str(opportunity_id))
        .maybe_single()
        .execute()
    )
    if resp and resp.data:
        return TrustScoreOut(**resp.data)
    return await compute_and_save_trust_score(opportunity_id)


async def get_trust_score(user_id: UUID) -> TrustScore:
    """Fetch or compute a user's trust score."""
    resp = (
        supabase_admin.table("trust_scores")
        .select("*")
        .eq("user_id", str(user_id))
        .single()
        .execute()
    )
    if resp.data:
        return TrustScore(**resp.data)

    # Compute from raw signals if no cached score exists
    return await _recompute_trust(user_id)


async def _recompute_trust(user_id: UUID) -> TrustScore:
    uid = str(user_id)

    # Count endorsements
    end_resp = (
        supabase_admin.table("endorsements")
        .select("id", count="exact")
        .eq("endorsed_user_id", uid)
        .execute()
    )
    endorsements = end_resp.count or 0

    # Count completed opportunities
    comp_resp = (
        supabase_admin.table("user_opportunities")
        .select("id", count="exact")
        .eq("user_id", uid)
        .eq("status", "completed")
        .execute()
    )
    completed = comp_resp.count or 0

    # Average peer rating
    rat_resp = (
        supabase_admin.table("ratings")
        .select("rating")
        .eq("rated_user_id", uid)
        .execute()
    )
    ratings_data = rat_resp.data or []
    avg_rating = (
        sum(r["rating"] for r in ratings_data) / len(ratings_data)
        if ratings_data
        else 0.0
    )

    raw_score = (
        endorsements * _ENDORSEMENT_WEIGHT
        + completed * _COMPLETION_WEIGHT
        + avg_rating * _RATING_WEIGHT
    )
    overall = min(raw_score, _MAX_SCORE)

    score_obj = TrustScore(
        user_id=user_id,
        overall_score=round(overall, 2),
        endorsements=endorsements,
        completed_opportunities=completed,
        peer_ratings_avg=round(avg_rating, 2),
    )

    # Upsert cached score
    supabase_admin.table("trust_scores").upsert(
        {"user_id": uid, **score_obj.model_dump(exclude={"user_id"})}
    ).execute()

    return score_obj


async def add_endorsement(endorser_id: UUID, data: EndorsementCreate) -> dict:
    """Record a skill endorsement and invalidate the target's cached score."""
    row = {
        "endorser_id": str(endorser_id),
        "endorsed_user_id": str(data.endorsed_user_id),
        "skill": data.skill,
        "note": data.note,
    }
    resp = supabase_admin.table("endorsements").insert(row).execute()
    # Invalidate cached trust score so next fetch recomputes
    supabase_admin.table("trust_scores").delete().eq(
        "user_id", str(data.endorsed_user_id)
    ).execute()
    return resp.data[0] if resp.data else {}


async def add_rating(rater_id: UUID, data: RatingCreate) -> dict:
    """Record a peer rating and invalidate the target's cached score."""
    row = {
        "rater_id": str(rater_id),
        "rated_user_id": str(data.rated_user_id),
        "opportunity_id": str(data.opportunity_id),
        "rating": data.rating,
        "review": data.review,
    }
    resp = supabase_admin.table("ratings").insert(row).execute()
    supabase_admin.table("trust_scores").delete().eq(
        "user_id", str(data.rated_user_id)
    ).execute()
    return resp.data[0] if resp.data else {}
