"""
Admin routes — /api/v1/admin

Administrative portal operations:
- GET    /admin/me              — Check admin status and role
- GET    /admin/metrics         — Aggregated platform metrics and KPIs
- GET    /admin/opportunities   — Search and list opportunities (with admin meta)
- DELETE /admin/opportunities/{id} — Delete an opportunity
- GET    /admin/students        — Search and list registered students
- GET    /admin/settings        — Fetch runtime app settings
- PATCH  /admin/settings        — Update a runtime setting (e.g. LLM provider)
- GET    /admin/roster          — List all authorized administrators
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from loguru import logger

from app.api.deps import AdminStudent
from app.core.supabase_client import supabase_admin
from app.models.base import APIResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class SettingUpdateRequest(BaseModel):
    key: str
    value: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/me", summary="Verify current user's admin access")
async def get_admin_me(admin: AdminStudent):
    """Returns the authenticated admin's role and details."""
    admin_record = (
        supabase_admin.table("admins")
        .select("*")
        .eq("email", admin.email.lower())
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    role = admin_record.data.get("role", "admin") if admin_record.data else "admin"

    return APIResponse(
        data={
            "id": admin.id,
            "email": admin.email,
            "name": admin.name,
            "role": role,
            "is_admin": True,
        },
        message="Admin privileges verified.",
    )


@router.get("/metrics", summary="Aggregated platform statistics and monitoring KPIs")
async def get_admin_metrics(admin: AdminStudent):
    """Calculates overview metrics across students, opportunities, events, and AI settings."""
    try:
        # Total students
        st_resp = supabase_admin.table("students").select("id", count="exact").execute()
        total_students = st_resp.count or len(st_resp.data or [])

        # Opportunities summary
        opp_resp = supabase_admin.table("opportunities").select("id, domain, type, is_active").execute()
        opps = opp_resp.data or []
        total_opportunities = len(opps)
        active_opportunities = sum(1 for o in opps if o.get("is_active", True))

        # Domain breakdown
        domain_counts: Dict[str, int] = {}
        type_counts: Dict[str, int] = {}
        for o in opps:
            dom = (o.get("domain") or "other").title()
            typ = (o.get("type") or "other").title()
            domain_counts[dom] = domain_counts.get(dom, 0) + 1
            type_counts[typ] = type_counts.get(typ, 0) + 1

        # Total events
        events_resp = supabase_admin.table("events").select("id", count="exact").execute()
        total_events = events_resp.count or len(events_resp.data or [])

        # App settings (LLM provider)
        settings_resp = supabase_admin.table("app_settings").select("*").execute()
        settings_map = {row["key"]: row["value"] for row in (settings_resp.data or [])}
        active_llm_provider = settings_map.get("LLM_PROVIDER", "gemini")

        # Admins count
        adm_resp = supabase_admin.table("admins").select("id", count="exact").eq("is_active", True).execute()
        total_admins = adm_resp.count or len(adm_resp.data or [])

        return APIResponse(
            data={
                "total_students": total_students,
                "total_opportunities": total_opportunities,
                "active_opportunities": active_opportunities,
                "total_events": total_events,
                "total_admins": total_admins,
                "active_llm_provider": active_llm_provider,
                "domain_distribution": domain_counts,
                "type_distribution": type_counts,
                "settings": settings_map,
            },
            message="Admin metrics loaded successfully.",
        )
    except Exception as exc:
        logger.error(f"Error compiling admin metrics: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admin metrics: {exc}",
        )


@router.get("/opportunities", summary="Search and list opportunities for admin")
async def list_admin_opportunities(
    admin: AdminStudent,
    q: Optional[str] = Query(None, description="Search keyword in title, organizer, or location"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    type: Optional[str] = Query(None, description="Filter by opportunity type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    """Lists opportunities with search and filtering for administrative oversight."""
    try:
        query = supabase_admin.table("opportunities").select(
            "id, title, description, domain, type, eligibility, deadline, location, organizer, source_url, is_active, created_at, updated_at",
            count="exact",
        )

        if domain and domain.lower() != "all":
            query = query.eq("domain", domain.lower())
        if type and type.lower() != "all":
            query = query.eq("type", type.lower())
        if q:
            clean_q = q.strip()
            query = query.or_(
                f"title.ilike.%{clean_q}%,organizer.ilike.%{clean_q}%,location.ilike.%{clean_q}%"
            )

        offset = (page - 1) * page_size
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
        resp = query.execute()

        items = resp.data or []
        total = resp.count or len(items)

        return APIResponse(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }
        )
    except Exception as exc:
        logger.error(f"Error fetching admin opportunities: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch opportunities: {exc}",
        )


@router.delete("/opportunities/{opportunity_id}", summary="Delete an opportunity")
async def delete_opportunity(
    opportunity_id: UUID,
    admin: AdminStudent,
):
    """Deletes an opportunity and associated event dependencies."""
    try:
        # Delete dependent events first
        supabase_admin.table("events").delete().eq("opportunity_id", str(opportunity_id)).execute()
        # Delete opportunity
        del_resp = supabase_admin.table("opportunities").delete().eq("id", str(opportunity_id)).execute()

        return APIResponse(
            data={"id": str(opportunity_id)},
            message=f"Opportunity {opportunity_id} deleted successfully.",
        )
    except Exception as exc:
        logger.error(f"Failed to delete opportunity {opportunity_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete opportunity: {exc}",
        )


@router.get("/students", summary="Search and list registered students")
async def list_admin_students(
    admin: AdminStudent,
    q: Optional[str] = Query(None, description="Search keyword in name, email, department, or location"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
):
    """Returns directory of students with profile details and skills for admin monitoring."""
    try:
        query = supabase_admin.table("students").select(
            "id, name, email, department, location, skills, interests, career_goals, avatar_url, is_active, created_at",
            count="exact",
        )

        if q:
            clean_q = q.strip()
            query = query.or_(
                f"name.ilike.%{clean_q}%,email.ilike.%{clean_q}%,department.ilike.%{clean_q}%,location.ilike.%{clean_q}%"
            )

        offset = (page - 1) * page_size
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)
        resp = query.execute()

        items = resp.data or []
        total = resp.count or len(items)

        return APIResponse(
            data={
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }
        )
    except Exception as exc:
        logger.error(f"Error fetching students: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch students: {exc}",
        )


@router.get("/settings", summary="Get runtime configuration settings")
async def get_admin_settings(admin: AdminStudent):
    """Lists key-value runtime configuration settings."""
    resp = supabase_admin.table("app_settings").select("*").execute()
    return APIResponse(data=resp.data or [])


@router.patch("/settings", summary="Update a runtime configuration setting")
async def update_admin_setting(
    body: SettingUpdateRequest,
    admin: AdminStudent,
):
    """Updates live configuration (e.g. LLM_PROVIDER between 'gemini' and 'ollama')."""
    try:
        resp = (
            supabase_admin.table("app_settings")
            .update({
                "value": body.value,
                "updated_by": admin.email,
            })
            .eq("key", body.key)
            .execute()
        )
        return APIResponse(
            data=resp.data,
            message=f"Setting '{body.key}' updated to '{body.value}'.",
        )
    except Exception as exc:
        logger.error(f"Failed to update setting {body.key}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {exc}",
        )


@router.get("/roster", summary="List platform administrators")
async def get_admin_roster(admin: AdminStudent):
    """Returns active administrator accounts."""
    resp = supabase_admin.table("admins").select("id, email, role, added_by, is_active, created_at").execute()
    return APIResponse(data=resp.data or [])
