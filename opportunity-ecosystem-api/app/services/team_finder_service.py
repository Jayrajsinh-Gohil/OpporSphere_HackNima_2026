"""
Team Finder service — suggest optimal team compositions for opportunities.
Uses embedding similarity to identify best-fit users per required role.
"""

from __future__ import annotations

from typing import List
from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_embedder
from app.services.team_finder import (
    create_team_invite,
    create_team_with_members,
    get_team_matches,
    infer_student_role,
    is_role_complementary,
)

__all__ = [
    "find_team",
    "get_team_matches",
    "create_team_invite",
    "create_team_with_members",
    "infer_student_role",
    "is_role_complementary",
]


async def find_team(request: TeamFinderRequest) -> TeamFinderResponse:
    """
    For each required role:
      1. Embed the role description.
      2. Retrieve all active user profiles with embeddings.
      3. Rank by cosine similarity and pick top-k.
      4. Exclude duplicates (one user per team).
    """
    embedder = get_embedder()

    # Fetch opportunity description for context
    opp_resp = (
        supabase_admin.table("opportunities")
        .select("title, description, required_skills")
        .eq("id", str(request.opportunity_id))
        .single()
        .execute()
    )
    opp = opp_resp.data or {}

    # Fetch all user profiles with embeddings
    users_resp = (
        supabase_admin.table("profiles")
        .select("id, full_name, avatar_url, skills, bio, embedding")
        .eq("is_active", True)
        .neq("id", str(request.user_id))  # exclude requester
        .execute()
    )
    users: list[dict] = users_resp.data or []

    # Fetch trust scores in bulk
    uid_strs = [u["id"] for u in users]
    trust_resp = (
        supabase_admin.table("trust_scores")
        .select("user_id, overall_score")
        .in_("user_id", uid_strs)
        .execute()
    )
    trust_map = {t["user_id"]: t["overall_score"] for t in (trust_resp.data or [])}

    selected_ids: set[str] = set()
    suggested_team: List[TeamMemberSuggestion] = []

    roles = request.required_roles or ["Team Member"]

    for role in roles:
        role_text = (
            f"Role: {role}. "
            f"Opportunity: {opp.get('title', '')}. "
            f"Description: {opp.get('description', '')}."
        )
        role_vector = await embedder.embed(role_text)

        # Score users for this role
        scored_users = []
        for user in users:
            if user["id"] in selected_ids:
                continue
            user_embedding = user.get("embedding")
            if not user_embedding:
                continue
            score = embedder.cosine_similarity(role_vector, user_embedding)
            scored_users.append((score, user))

        scored_users.sort(key=lambda x: x[0], reverse=True)

        for score, user in scored_users[: request.top_k_per_role]:
            selected_ids.add(user["id"])
            suggested_team.append(
                TeamMemberSuggestion(
                    user_id=user["id"],
                    full_name=user.get("full_name", "Unknown"),
                    avatar_url=user.get("avatar_url"),
                    role=role,
                    match_score=round(score, 4),
                    skills=user.get("skills", []),
                    trust_score=trust_map.get(user["id"], 0.0),
                )
            )

        if len(suggested_team) >= request.team_size:
            break

    return TeamFinderResponse(
        opportunity_id=request.opportunity_id,
        suggested_team=suggested_team[: request.team_size],
    )
