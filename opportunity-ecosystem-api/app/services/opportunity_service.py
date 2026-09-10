"""
Opportunity service — CRUD + filtered/paginated listing.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.models.opportunity import (
    EventCreate,
    EventOut,
    OpportunityCreate,
    OpportunityDomain,
    OpportunityOut,
    OpportunitySummary,
    OpportunityType,
    OpportunityUpdate,
)
from app.services.match import embed_and_store_opportunity
from app.services.trust import compute_and_save_trust_score


# ─────────────────────────────────────────────────────────────────────────────
# READ — list with filters + pagination
# ─────────────────────────────────────────────────────────────────────────────

async def list_opportunities(
    domain: Optional[OpportunityDomain] = None,
    type_: Optional[OpportunityType] = None,
    location: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Return a paginated, filtered list from the `opportunity_summary` view.
    Filters applied server-side via Supabase PostgREST query operators.
    """
    query = (
        supabase_admin.table("opportunity_summary")
        .select("*", count="exact")
        .eq("is_active", True)
        .eq("is_duplicate", False)
    )

    if domain:
        query = query.eq("domain", domain.value)
    if type_:
        query = query.eq("type", type_.value)
    if location:
        # Case-insensitive partial match
        query = query.ilike("location", f"%{location}%")

    # Order by trust score descending so high-quality opportunities surface first
    query = query.order("trust_score", desc=True).order("created_at", desc=True)

    # Pagination
    start = (page - 1) * page_size
    query = query.range(start, start + page_size - 1)

    resp = query.execute()
    total = resp.count or 0
    items = [OpportunitySummary(**row) for row in (resp.data or [])]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, -(-total // page_size)),  # ceiling division
    }


# ─────────────────────────────────────────────────────────────────────────────
# READ — single opportunity
# ─────────────────────────────────────────────────────────────────────────────

async def get_opportunity(opportunity_id: UUID) -> OpportunitySummary | None:
    """Fetch one opportunity with its trust signals."""
    resp = (
        supabase_admin.table("opportunity_summary")
        .select("*")
        .eq("id", str(opportunity_id))
        .maybe_single()
        .execute()
    )
    if not resp.data:
        return None
    return OpportunitySummary(**resp.data)


# ─────────────────────────────────────────────────────────────────────────────
# CREATE — opportunity
# ─────────────────────────────────────────────────────────────────────────────

async def create_opportunity(data: OpportunityCreate) -> OpportunityOut:
    """
    Insert a new opportunity and immediately compute + store its embedding.
    The embedding is built from: title + description + eligibility.
    """
    new_id = uuid4()
    row = data.model_dump(exclude_none=True)
    row["id"] = str(new_id)

    # Serialize date fields to ISO string for Supabase
    if row.get("deadline"):
        row["deadline"] = row["deadline"].isoformat()

    # Serialize enum fields to string values
    if "domain" in row:
        row["domain"] = row["domain"].value if hasattr(row["domain"], "value") else row["domain"]
    if "type" in row:
        row["type"] = row["type"].value if hasattr(row["type"], "value") else row["type"]

    resp = supabase_admin.table("opportunities").insert(row).execute()
    if not resp.data:
        raise ValueError("Opportunity insert returned no data.")

    # Embed asynchronously & compute trust score
    logger.info(f"Opportunity created: {new_id} — queuing embedding and trust scan")
    await _embed_opportunity(new_id, data)
    try:
        await compute_and_save_trust_score(new_id)
    except Exception as exc:
        logger.error(f"Trust scan failed for {new_id}: {exc}")

    return created


async def _embed_opportunity(opportunity_id: UUID, data: OpportunityCreate) -> None:
    """Compute and persist the opportunity embedding vector using sentence-transformers."""
    await embed_and_store_opportunity(opportunity_id, data)


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE — opportunity (admin)
# ─────────────────────────────────────────────────────────────────────────────

async def update_opportunity(
    opportunity_id: UUID, data: OpportunityUpdate
) -> OpportunityOut:
    updates = data.model_dump(exclude_none=True)
    if not updates:
        raise ValueError("No fields provided for update.")

    if "deadline" in updates and updates["deadline"]:
        updates["deadline"] = updates["deadline"].isoformat()
    if "domain" in updates and hasattr(updates["domain"], "value"):
        updates["domain"] = updates["domain"].value
    if "type" in updates and hasattr(updates["type"], "value"):
        updates["type"] = updates["type"].value

    resp = (
        supabase_admin.table("opportunities")
        .update(updates)
        .eq("id", str(opportunity_id))
        .execute()
    )
    if not resp.data:
        raise ValueError("Opportunity not found or update failed.")

    # Re-embed if the text content changed
    text_fields = {"title", "description", "eligibility", "organizer"}
    if text_fields & updates.keys():
        full_resp = (
            supabase_admin.table("opportunities")
            .select("title, description, eligibility, organizer")
            .eq("id", str(opportunity_id))
            .single()
            .execute()
        )
        opp_data = full_resp.data or {}
        dummy = OpportunityCreate(
            title=opp_data.get("title", ""),
            description=opp_data.get("description", ""),
            eligibility=opp_data.get("eligibility"),
            organizer=opp_data.get("organizer"),
        )
        await _embed_opportunity(opportunity_id, dummy)

    return OpportunityOut(**resp.data[0])


# ─────────────────────────────────────────────────────────────────────────────
# EVENTS CRUD
# ─────────────────────────────────────────────────────────────────────────────

async def create_event(data: EventCreate) -> EventOut:
    row = data.model_dump()
    row["opportunity_id"] = str(row["opportunity_id"])
    row["status"] = row["status"].value if hasattr(row["status"], "value") else row["status"]

    resp = supabase_admin.table("events").insert(row).execute()
    if not resp.data:
        raise ValueError("Event insert returned no data.")
    return EventOut(**resp.data[0])


async def list_events(opportunity_id: UUID) -> list[EventOut]:
    resp = (
        supabase_admin.table("events")
        .select("*")
        .eq("opportunity_id", str(opportunity_id))
        .order("created_at", desc=True)
        .execute()
    )
    return [EventOut(**row) for row in (resp.data or [])]
