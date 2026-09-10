"""
Match service — embedding generation and opportunity recommendations.

Implements Phase B3:
  1. Profile embedding hook on create/update:
     Concatenates skills + interests + career_goals, encodes via sentence-transformers
     (all-MiniLM-L6-v2, dim=384), stores into `students.embedding`.
  2. Opportunity embedding hook on create:
     Encodes title + description + eligibility + domain + type + organizer,
     stores into `opportunities.embedding`.
  3. Recommendation query:
     Cosine similarity search (ORDER BY embedding <=> student_embedding LIMIT 10)
     via Supabase pgvector RPC / query with fallback weighting for students
     without interaction history.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_local_embedder
from app.models.match import RecommendationItem, RecommendationsResponse
from app.models.opportunity import OpportunityCreate


# ── Text Preparation Helpers ──────────────────────────────────────────────────

def build_student_embed_text(
    skills: Optional[List[str]] = None,
    interests: Optional[List[str]] = None,
    career_goals: Optional[str] = None,
) -> str:
    """Concatenate skills + interests + career_goals into a single semantic string."""
    parts: List[str] = []
    if skills:
        cleaned_skills = [s.strip() for s in skills if s and s.strip()]
        if cleaned_skills:
            parts.append(f"Skills: {', '.join(cleaned_skills)}")
    if interests:
        cleaned_interests = [i.strip() for i in interests if i and i.strip()]
        if cleaned_interests:
            parts.append(f"Interests: {', '.join(cleaned_interests)}")
    if career_goals and career_goals.strip():
        parts.append(f"Career Goals: {career_goals.strip()}")

    return " | ".join(parts).strip()


def build_opportunity_embed_text(data: OpportunityCreate | Dict[str, Any]) -> str:
    """Concatenate opportunity details into a single semantic string."""
    if isinstance(data, OpportunityCreate):
        d = data.model_dump()
    else:
        d = dict(data)

    parts: List[str] = []
    if d.get("title"):
        parts.append(f"Title: {d['title']}")
    if d.get("description"):
        parts.append(f"Description: {d['description']}")
    if d.get("domain"):
        domain_val = d["domain"].value if hasattr(d["domain"], "value") else d["domain"]
        parts.append(f"Domain: {domain_val}")
    if d.get("type"):
        type_val = d["type"].value if hasattr(d["type"], "value") else d["type"]
        parts.append(f"Type: {type_val}")
    if d.get("eligibility"):
        parts.append(f"Eligibility: {d['eligibility']}")
    if d.get("organizer"):
        parts.append(f"Organizer: {d['organizer']}")

    return " | ".join(parts).strip()


# ── Embedding Persistence Hooks ───────────────────────────────────────────────

async def embed_and_store_student(
    student_id: UUID,
    skills: Optional[List[str]] = None,
    interests: Optional[List[str]] = None,
    career_goals: Optional[str] = None,
) -> Optional[List[float]]:
    """
    Generate an embedding from skills+interests+career_goals and save to `students.embedding`.
    Uses local sentence-transformers (all-MiniLM-L6-v2, 384 dimensions).
    """
    text = build_student_embed_text(skills, interests, career_goals)
    if not text:
        logger.info(f"Student {student_id} has no skills/interests/goals to embed. Skipping.")
        return None

    try:
        embedder = get_local_embedder()
        vector = await embedder.embed(text)

        supabase_admin.table("students").update(
            {"embedding": vector}
        ).eq("id", str(student_id)).execute()

        logger.info(f"Generated & stored 384-dim embedding for student {student_id}")
        return vector
    except Exception as exc:
        logger.error(f"Failed to embed student {student_id}: {exc}")
        return None


async def embed_and_store_opportunity(
    opportunity_id: UUID,
    data: OpportunityCreate | Dict[str, Any],
) -> Optional[List[float]]:
    """
    Generate an embedding for an opportunity and save to `opportunities.embedding`.
    """
    text = build_opportunity_embed_text(data)
    if not text:
        logger.warning(f"Opportunity {opportunity_id} text is empty. Skipping embedding.")
        return None

    try:
        embedder = get_local_embedder()
        vector = await embedder.embed(text)

        supabase_admin.table("opportunities").update(
            {"embedding": vector}
        ).eq("id", str(opportunity_id)).execute()

        logger.info(f"Generated & stored 384-dim embedding for opportunity {opportunity_id}")
        return vector
    except Exception as exc:
        logger.error(f"Failed to embed opportunity {opportunity_id}: {exc}")
        return None


# ── Interaction History Check ─────────────────────────────────────────────────

async def check_student_interaction_history(student_id: UUID) -> bool:
    """
    Check if the student has any interaction history:
      - Submitted or draft applications in `applications` table
      - Team memberships in `team_members` table
    """
    sid = str(student_id)
    try:
        app_resp = (
            supabase_admin.table("applications")
            .select("id", count="exact")
            .eq("student_id", sid)
            .limit(1)
            .execute()
        )
        if (app_resp.count or 0) > 0:
            return True

        tm_resp = (
            supabase_admin.table("team_members")
            .select("id", count="exact")
            .eq("student_id", sid)
            .limit(1)
            .execute()
        )
        if (tm_resp.count or 0) > 0:
            return True

        return False
    except Exception as exc:
        logger.warning(f"Could not check interaction history for {student_id}: {exc}")
        return False


# ── Recommendation Engine ─────────────────────────────────────────────────────

async def get_recommendations(
    student_id: UUID,
    top_k: int = 10,
    min_score: float = 0.0,
) -> RecommendationsResponse:
    """
    Fetch personalized opportunity recommendations for the logged-in student.
    
    Workflow:
      1. Retrieve student profile and embedding.
      2. If student has profile text but no embedding, compute and store it.
      3. Check student interaction history.
      4. If student has an embedding:
           Run pgvector cosine similarity search (ORDER BY embedding <=> student_embedding LIMIT top_k)
           via the Supabase RPC `match_opportunities`.
           If student has no interaction history, weight recent/popular/high-trust opportunities higher.
      5. Fallback path (no student embedding):
           Return top recent/popular opportunities from `opportunity_summary` view
           ranked by trust score and recency.
    """
    sid = str(student_id)

    # 1. Fetch student info
    student_resp = (
        supabase_admin.table("students")
        .select("id, skills, interests, career_goals, embedding")
        .eq("id", sid)
        .maybe_single()
        .execute()
    )
    student_data = student_resp.data if student_resp else None
    student_embedding: Optional[List[float]] = (
        student_data.get("embedding") if student_data else None
    )

    # Auto-generate embedding if missing but profile text exists
    if not student_embedding and student_data:
        skills = student_data.get("skills") or []
        interests = student_data.get("interests") or []
        career_goals = student_data.get("career_goals")
        if skills or interests or career_goals:
            student_embedding = await embed_and_store_student(
                student_id, skills, interests, career_goals
            )

    has_embedding = bool(student_embedding)
    has_history = await check_student_interaction_history(student_id)

    # 2. Embedding-based recommendation path
    if has_embedding and student_embedding:
        try:
            # Query pgvector via Supabase RPC function created in V009:
            # match_opportunities(query_embedding vector(384), top_k int, min_score float)
            rpc_resp = supabase_admin.rpc(
                "match_opportunities",
                {
                    "query_embedding": student_embedding,
                    "top_k": max(top_k * 2, 20),
                    "min_score": min_score,
                },
            ).execute()
            raw_matches = rpc_resp.data or []
        except Exception as rpc_exc:
            logger.warning(f"RPC match_opportunities failed or unavailable ({rpc_exc}). Falling back to query fetch.")
            raw_matches = await _fallback_vector_search(student_embedding, top_k=max(top_k * 2, 20), min_score=min_score)

        if raw_matches:
            recommendations = _rank_and_score_matches(
                raw_matches=raw_matches,
                has_history=has_history,
                top_k=top_k,
            )
            return RecommendationsResponse(
                student_id=student_id,
                has_profile_embedding=True,
                has_interaction_history=has_history,
                recommendations=recommendations,
                total=len(recommendations),
            )

    # 3. Cold-start Fallback path (no profile embedding or zero vector matches)
    fallback_items = await _get_cold_start_opportunities(top_k=top_k)
    return RecommendationsResponse(
        student_id=student_id,
        has_profile_embedding=has_embedding,
        has_interaction_history=has_history,
        recommendations=fallback_items,
        total=len(fallback_items),
    )


def _rank_and_score_matches(
    raw_matches: List[Dict[str, Any]],
    has_history: bool,
    top_k: int,
) -> List[RecommendationItem]:
    """
    Ranks matches and computes 'match relevance %'.
    If `has_history` is False, applies a popularity/recency/trust weight.
    """
    scored_items: List[Dict[str, Any]] = []

    for item in raw_matches:
        sim = float(item.get("similarity", 0.0))
        sim = max(0.0, min(1.0, sim))  # clamp to [0, 1]
        trust = int(item.get("trust_score") or 0)
        trust_norm = max(0.0, min(1.0, trust / 100.0))

        if not has_history:
            # Fallback weighting for students without interaction history:
            # Weight recent/popular/trusted opportunities higher:
            # 60% semantic similarity + 30% trust/quality + 10% recency baseline
            blended = (0.60 * sim) + (0.30 * trust_norm) + 0.10
            final_score = max(0.0, min(1.0, blended))
            reason = "Recommended based on profile similarity, boosted by community trust and popularity"
        else:
            final_score = sim
            reason = "Direct match with your skills, interests, and career goals"

        match_relevance_pct = round(final_score * 100.0, 1)

        scored_items.append({
            "id": item["id"],
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "domain": item.get("domain"),
            "type": item.get("type"),
            "location": item.get("location"),
            "organizer": item.get("organizer"),
            "deadline": str(item["deadline"]) if item.get("deadline") else None,
            "trust_score": trust,
            "similarity": round(sim, 4),
            "match_relevance_pct": match_relevance_pct,
            "is_fallback": not has_history,
            "reason": reason,
            "_sort_key": final_score,
        })

    # Sort descending by final score
    scored_items.sort(key=lambda x: x["_sort_key"], reverse=True)
    top_items = scored_items[:top_k]

    return [
        RecommendationItem(
            id=item["id"],
            title=item["title"],
            description=item["description"],
            domain=item["domain"],
            type=item["type"],
            location=item["location"],
            organizer=item["organizer"],
            deadline=item["deadline"],
            trust_score=item["trust_score"],
            similarity=item["similarity"],
            match_relevance_pct=item["match_relevance_pct"],
            is_fallback=item["is_fallback"],
            reason=item["reason"],
        )
        for item in top_items
    ]


async def _fallback_vector_search(
    query_vector: List[float],
    top_k: int = 20,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    """In-memory cosine calculation fallback if Supabase RPC is not provisioned yet."""
    embedder = get_local_embedder()
    resp = (
        supabase_admin.table("opportunities")
        .select("id, title, description, domain, type, location, organizer, deadline, embedding")
        .eq("is_active", True)
        .not_.is_("embedding", "null")
        .execute()
    )
    rows = resp.data or []
    scored = []
    for row in rows:
        emb = row.get("embedding")
        if not emb:
            continue
        sim = embedder.cosine_similarity(query_vector, emb)
        if sim >= min_score:
            scored.append({**row, "similarity": sim, "trust_score": 50})

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_k]


async def _get_cold_start_opportunities(top_k: int = 10) -> List[RecommendationItem]:
    """
    Fallback for students without embedding:
    Return opportunities from `opportunity_summary` ordered by trust_score DESC, created_at DESC.
    """
    try:
        resp = (
            supabase_admin.table("opportunity_summary")
            .select("*")
            .eq("is_active", True)
            .order("trust_score", desc=True)
            .order("created_at", desc=True)
            .limit(top_k)
            .execute()
        )
        rows = resp.data or []
    except Exception as exc:
        logger.warning(f"Failed to query opportunity_summary view: {exc}. Querying opportunities table directly.")
        resp = (
            supabase_admin.table("opportunities")
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(top_k)
            .execute()
        )
        rows = resp.data or []

    items: List[RecommendationItem] = []
    for idx, row in enumerate(rows):
        trust = int(row.get("trust_score") or 70)
        # Cold-start baseline relevance percentage: based on trust score and rank
        relevance = round(max(50.0, min(95.0, trust * 0.85 + (top_k - idx) * 1.5)), 1)
        sim = round(relevance / 100.0, 4)

        items.append(
            RecommendationItem(
                id=row["id"],
                title=row.get("title", ""),
                description=row.get("description", ""),
                domain=row.get("domain"),
                type=row.get("type"),
                location=row.get("location"),
                organizer=row.get("organizer"),
                deadline=str(row["deadline"]) if row.get("deadline") else None,
                trust_score=trust,
                similarity=sim,
                match_relevance_pct=relevance,
                is_fallback=True,
                reason="Popular & verified opportunity (complete your profile skills for personalized AI match)",
            )
        )

    return items
