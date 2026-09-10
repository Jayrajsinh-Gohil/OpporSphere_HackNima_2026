"""
Discovery service — search and recommend opportunities.
Supports free-text semantic search, category/tag filtering, and pagination.
"""

from __future__ import annotations

from typing import List

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_embedder
from app.services.discovery import (
    extract_search_entities,
    parse_time_constraint,
    smart_search,
)

__all__ = [
    "discover_opportunities",
    "smart_search",
    "extract_search_entities",
    "parse_time_constraint",
]


async def discover_opportunities(request: DiscoveryRequest) -> DiscoveryResponse:
    """
    Hybrid discovery:
      - If a free-text query is provided → embed it and rank by cosine similarity.
      - Always apply category / tag filters (server-side, Supabase query).
      - Paginate the final result set.
    """
    embedder = get_embedder()

    # ── Build Supabase query ────────────────────────────────────────────────────
    query = (
        supabase_admin.table("opportunities")
        .select("id, title, description, category, tags, source_url, deadline, embedding")
        .eq("is_active", True)
    )

    if request.categories:
        query = query.in_("category", request.categories)

    # Tag filtering: check if any requested tag is in the tags array
    # Supabase PostgREST supports `cs` (contains) for array columns
    if request.tags:
        query = query.contains("tags", request.tags)

    raw_resp = query.execute()
    all_opps: list[dict] = raw_resp.data or []

    # ── Semantic ranking ────────────────────────────────────────────────────────
    if request.query:
        query_vector = await embedder.embed(request.query)
        for opp in all_opps:
            opp_embedding = opp.get("embedding")
            opp["_score"] = (
                embedder.cosine_similarity(query_vector, opp_embedding)
                if opp_embedding
                else 0.0
            )
        all_opps.sort(key=lambda x: x["_score"], reverse=True)
    else:
        for opp in all_opps:
            opp["_score"] = 0.0

    # ── Pagination ──────────────────────────────────────────────────────────────
    total = len(all_opps)
    start = (request.page - 1) * request.page_size
    end = start + request.page_size
    page_opps = all_opps[start:end]

    results: List[DiscoveredOpportunity] = [
        DiscoveredOpportunity(
            id=opp["id"],
            title=opp["title"],
            description=opp["description"],
            category=opp.get("category"),
            tags=opp.get("tags", []),
            relevance_score=round(opp["_score"], 4),
            source_url=opp.get("source_url"),
            deadline=opp.get("deadline"),
        )
        for opp in page_opps
    ]

    return DiscoveryResponse(
        results=results,
        total=total,
        page=request.page,
        page_size=request.page_size,
    )
