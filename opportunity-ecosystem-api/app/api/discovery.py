"""
Discovery routes — /api/v1/discovery & /api/discovery

Implements Phase B7:
  - POST /api/discovery/search: Natural language search over opportunities using
    spaCy NER + EntityRuler, mapping to structured Supabase filters with pgvector
    semantic search fallback.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import get_current_user
from app.models.base import APIResponse
from app.models.discovery import (
    DiscoveryRequest,
    DiscoveryResponse,
    SmartSearchRequest,
    SmartSearchResponse,
)
from app.services import discovery, discovery_service

router = APIRouter(prefix="/discovery", tags=["Discovery"])


# ── Phase B7: Natural-Language Smart Discovery ────────────────────────────────

@router.post(
    "/search",
    response_model=APIResponse[SmartSearchResponse],
    summary="Natural language opportunity search",
    description=(
        "Uses spaCy with a custom EntityRuler to extract domain, location, "
        "student type/department, and temporal constraints ('this month', 'next week') "
        "from a free-form query. Maps extracted entities to structured filters "
        "(domain ILIKE, location ILIKE, deadline BETWEEN). Falls back to a pgvector "
        "semantic similarity search if extraction confidence is low or structured filters "
        "yield 0 matches."
    ),
)
async def smart_search_opportunities(
    body: SmartSearchRequest,
    _claims: dict = Depends(get_current_user),
):
    try:
        search_result = await discovery.smart_search(
            query=body.query,
            top_k=body.top_k,
        )
        return APIResponse(
            data=search_result,
            message=(
                f"Found {search_result.total} opportunities using "
                f"{search_result.search_mode} (confidence: {search_result.confidence_score})."
            ),
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Smart discovery search failed: {exc}",
        )


# ── Legacy Endpoint Compatibility ─────────────────────────────────────────────

@router.post(
    "/",
    response_model=APIResponse[DiscoveryResponse],
    summary="Discover opportunities via semantic search and filters (legacy)",
)
async def discover(
    body: DiscoveryRequest,
    _claims: dict = Depends(get_current_user),
):
    try:
        result = await discovery_service.discover_opportunities(body)
        return APIResponse(data=result)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
