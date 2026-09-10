"""
Match service — semantic matching between user profiles and opportunities.
Uses embedding similarity to rank opportunities.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_embedder, get_local_embedder
from app.ml.llm_client import get_llm_client
from app.models.match import MatchRequest, MatchResponse, MatchResult
from app.services.match import (
    embed_and_store_opportunity,
    embed_and_store_student,
    get_recommendations,
)


async def match_opportunities(request: MatchRequest) -> MatchResponse:
    """
    1. Fetch user profile + skills from DB.
    2. Embed the user's skill/bio text.
    3. Fetch opportunity embeddings from Supabase.
    4. Cosine-rank opportunities; filter by min_score.
    5. Use LLM to generate a short explanation for top matches.
    """
    embedder = get_embedder()
    llm = get_llm_client()

    # ── 1. Fetch user profile ─────────────────────────────────────────────────
    profile_resp = (
        supabase_admin.table("profiles")
        .select("full_name, bio, skills, interests")
        .eq("id", str(request.user_id))
        .single()
        .execute()
    )
    profile = profile_resp.data or {}
    user_text = _build_user_text(profile)

    # ── 2. Embed user text ─────────────────────────────────────────────────────
    user_vector = await embedder.embed(user_text)

    # ── 3. Fetch opportunities ─────────────────────────────────────────────────
    query = supabase_admin.table("opportunities").select(
        "id, title, description, required_skills, preferred_skills, embedding"
    ).eq("is_active", True)

    if request.opportunity_id:
        query = query.eq("id", str(request.opportunity_id))

    opps_resp = query.execute()
    opportunities = opps_resp.data or []

    # ── 4. Score & filter ─────────────────────────────────────────────────────
    scored: list[dict] = []
    for opp in opportunities:
        opp_embedding = opp.get("embedding")
        if not opp_embedding:
            continue
        score = embedder.cosine_similarity(user_vector, opp_embedding)
        if score >= request.min_score:
            scored.append({**opp, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[: request.top_k]

    # ── 5. Build results with LLM explanation ─────────────────────────────────
    user_skills: list[str] = profile.get("skills", [])
    results: List[MatchResult] = []

    for item in top:
        req_skills: list[str] = item.get("required_skills", [])
        matched = [s for s in user_skills if s in req_skills]
        missing = [s for s in req_skills if s not in user_skills]

        explanation = await _generate_match_explanation(
            llm,
            user_text=user_text,
            opp_title=item["title"],
            match_score=item["score"],
            matched_skills=matched,
            missing_skills=missing,
        )

        results.append(
            MatchResult(
                opportunity_id=item["id"],
                title=item["title"],
                description=item["description"],
                match_score=round(item["score"], 4),
                matched_skills=matched,
                missing_skills=missing,
                explanation=explanation,
            )
        )

    return MatchResponse(
        user_id=request.user_id, results=results, total=len(results)
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_user_text(profile: dict) -> str:
    parts = []
    if profile.get("bio"):
        parts.append(profile["bio"])
    if profile.get("skills"):
        parts.append("Skills: " + ", ".join(profile["skills"]))
    if profile.get("interests"):
        parts.append("Interests: " + ", ".join(profile["interests"]))
    return " | ".join(parts) or "General user profile"


async def _generate_match_explanation(
    llm,
    user_text: str,
    opp_title: str,
    match_score: float,
    matched_skills: list,
    missing_skills: list,
) -> str:
    prompt = (
        f"User profile: {user_text}\n"
        f"Opportunity: {opp_title}\n"
        f"Match score: {match_score:.0%}\n"
        f"Matched skills: {', '.join(matched_skills) or 'none'}\n"
        f"Missing skills: {', '.join(missing_skills) or 'none'}\n\n"
        "Write a 2-sentence explanation of why this opportunity is a good match "
        "and one actionable improvement tip. Be concise and encouraging."
    )
    try:
        return await llm.chat(prompt, temperature=0.5, max_tokens=150)
    except Exception as exc:
        logger.warning(f"LLM explanation failed: {exc}")
        return f"Match score: {match_score:.0%}"


async def embed_and_store_opportunity(opportunity_id: UUID, text: str) -> None:
    """Embed an opportunity's text and persist the vector to Supabase."""
    embedder = get_embedder()
    vector = await embedder.embed(text)
    supabase_admin.table("opportunities").update({"embedding": vector}).eq(
        "id", str(opportunity_id)
    ).execute()
    logger.info(f"Embedded opportunity {opportunity_id}")
