"""
Discovery service — AI Smart Discovery (Phase B7).

Implements:
  1. spaCy NLP pipeline with a custom EntityRuler:
     Extracts from natural language queries:
       - domain / keyword
       - location
       - student type / department
       - time constraints ("this month", "next week", etc. -> date range)
  2. Maps extracted entities into structured Supabase queries:
     (domain ILIKE, location ILIKE, deadline BETWEEN, type ILIKE).
  3. Low-confidence fallback:
     Falls back to pgvector semantic cosine similarity search against opportunity embeddings.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from functools import lru_cache
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from loguru import logger
import spacy
from spacy.language import Language

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_local_embedder
from app.models.discovery import (
    DiscoveredOpportunityItem,
    ExtractedFilters,
    SmartSearchResponse,
)

# Confidence threshold to decide between structured query vs semantic fallback
CONFIDENCE_THRESHOLD = 0.5


# ── Domain Mapping Dictionary ─────────────────────────────────────────────────

_DOMAIN_CANONICAL: Dict[str, str] = {
    "ai": "technology",
    "artificial intelligence": "technology",
    "machine learning": "technology",
    "ml": "technology",
    "deep learning": "technology",
    "nlp": "technology",
    "computer vision": "technology",
    "web": "technology",
    "web dev": "technology",
    "web development": "technology",
    "software": "technology",
    "coding": "technology",
    "programming": "technology",
    "cloud": "technology",
    "cybersecurity": "technology",
    "data science": "technology",
    "technology": "technology",
    "tech": "technology",
    "science": "science",
    "biology": "science",
    "physics": "science",
    "chemistry": "science",
    "genomics": "science",
    "scientific": "science",
    "arts": "arts",
    "design": "arts",
    "ui/ux": "arts",
    "ui": "arts",
    "ux": "arts",
    "creative": "arts",
    "business": "business",
    "startup": "business",
    "startups": "business",
    "finance": "business",
    "fintech": "business",
    "venture": "business",
    "marketing": "business",
    "entrepreneurship": "business",
    "social impact": "social_impact",
    "social": "social_impact",
    "community": "social_impact",
    "ngo": "social_impact",
    "civic": "social_impact",
    "health": "health",
    "healthcare": "health",
    "medical": "health",
    "biotech": "health",
    "education": "education",
    "edtech": "education",
    "teaching": "education",
    "learning": "education",
    "environment": "environment",
    "climate": "environment",
    "climate change": "environment",
    "sustainability": "environment",
    "green": "environment",
    "clean energy": "environment",
}


# ── spaCy Pipeline Singleton ──────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_discovery_nlp() -> Language:
    """
    Initializes and caches the spaCy NLP pipeline with a custom EntityRuler
    specifically tuned for opportunity discovery patterns.
    """
    logger.info("Initializing spaCy pipeline (en_core_web_sm) with custom EntityRuler...")
    nlp = spacy.load("en_core_web_sm")

    ruler = nlp.add_pipe("entity_ruler", before="ner", config={"overwrite_ents": True})

    patterns = []

    # 1. DOMAIN patterns
    for kw in _DOMAIN_CANONICAL.keys():
        tokens = kw.split()
        if len(tokens) == 1:
            patterns.append({"label": "DOMAIN", "pattern": [{"LOWER": tokens[0]}]})
        else:
            patterns.append({"label": "DOMAIN", "pattern": [{"LOWER": t} for t in tokens]})

    # 2. OPPORTUNITY TYPE patterns
    opp_types = {
        "hackathon": ["hackathon", "hackathons", "hack"],
        "internship": ["internship", "internships", "summer internship", "co-op"],
        "workshop": ["workshop", "workshops", "bootcamp", "training", "masterclass"],
        "competition": ["competition", "competitions", "contest", "challenge"],
        "fellowship": ["fellowship", "fellowships", "scholarship", "scholarships"],
        "grant": ["grant", "grants", "funding"],
    }
    for o_type, aliases in opp_types.items():
        for alias in aliases:
            tokens = alias.split()
            patterns.append({
                "label": "OPPORTUNITY_TYPE",
                "pattern": [{"LOWER": t} for t in tokens],
                "id": o_type,
            })

    # 3. LOCATION patterns
    locations = [
        "bengaluru", "bangalore", "hyderabad", "delhi", "new delhi", "mumbai",
        "pune", "chennai", "kolkata", "noida", "gurugram", "gurgaon",
        "online", "remote", "virtual", "hybrid", "india", "usa", "us",
    ]
    for loc in locations:
        tokens = loc.split()
        patterns.append({"label": "LOCATION", "pattern": [{"LOWER": t} for t in tokens]})

    # 4. STUDENT TYPE / DEPARTMENT patterns
    dept_keywords = [
        "computer science", "cs", "software engineering", "electrical", "ece",
        "mechanical", "information technology", "it", "undergraduate", "undergrad",
        "undergrads", "btech", "b.tech", "mtech", "m.tech", "postgraduate",
        "phd", "college student", "college students", "freshers", "students",
    ]
    for dept in dept_keywords:
        tokens = dept.split()
        patterns.append({"label": "STUDENT_TYPE", "pattern": [{"LOWER": t} for t in tokens]})

    # 5. TIME CONSTRAINT patterns
    time_phrases = [
        "this month", "next month", "this week", "next week",
        "in 2 weeks", "in two weeks", "in 3 weeks", "in three weeks",
        "next 30 days", "in 30 days", "upcoming", "this year", "today", "tomorrow",
    ]
    for phrase in time_phrases:
        tokens = phrase.split()
        patterns.append({"label": "TIME_CONSTRAINT", "pattern": [{"LOWER": t} for t in tokens]})

    ruler.add_patterns(patterns)
    logger.info(f"spaCy EntityRuler loaded with {len(patterns)} patterns.")
    return nlp


# ── Time Constraint Parser ────────────────────────────────────────────────────

def parse_time_constraint(
    phrase: str,
    ref_date: Optional[date] = None,
) -> Tuple[Optional[date], Optional[date]]:
    """
    Converts natural language temporal phrases into an explicit [start_date, end_date] range.
    """
    if ref_date is None:
        ref_date = date.today()

    p = phrase.lower().strip()

    if "this week" in p:
        start = ref_date
        days_until_sunday = 6 - ref_date.weekday()
        end = ref_date + timedelta(days=days_until_sunday)
        return start, end

    if "next week" in p:
        days_until_next_monday = 7 - ref_date.weekday()
        start = ref_date + timedelta(days=days_until_next_monday)
        end = start + timedelta(days=6)
        return start, end

    if "this month" in p:
        start = ref_date
        last_day = calendar.monthrange(ref_date.year, ref_date.month)[1]
        end = date(ref_date.year, ref_date.month, last_day)
        return start, end

    if "next month" in p:
        year = ref_date.year + (1 if ref_date.month == 12 else 0)
        month = 1 if ref_date.month == 12 else ref_date.month + 1
        start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end = date(year, month, last_day)
        return start, end

    if "in 2 weeks" in p or "in two weeks" in p:
        start = ref_date
        end = ref_date + timedelta(days=14)
        return start, end

    if "in 3 weeks" in p or "in three weeks" in p:
        start = ref_date
        end = ref_date + timedelta(days=21)
        return start, end

    if "30 days" in p:
        start = ref_date
        end = ref_date + timedelta(days=30)
        return start, end

    if "upcoming" in p or "this year" in p:
        start = ref_date
        end = ref_date + timedelta(days=90)
        return start, end

    if "tomorrow" in p:
        d = ref_date + timedelta(days=1)
        return d, d

    if "today" in p:
        return ref_date, ref_date

    return None, None


# ── Entity Extraction & Confidence Scoring ────────────────────────────────────

def extract_search_entities(
    query: str,
    ref_date: Optional[date] = None,
) -> Tuple[ExtractedFilters, float]:
    """
    Applies spaCy pipeline to extract domains, locations, departments, opportunity types,
    and temporal constraints. Computes a confidence score in [0.0, 1.0].
    """
    nlp = get_discovery_nlp()
    doc = nlp(query)

    raw_entities: Dict[str, List[str]] = {}
    extracted_domain: Optional[str] = None
    extracted_location: Optional[str] = None
    extracted_dept: Optional[str] = None
    extracted_type: Optional[str] = None
    deadline_from: Optional[date] = None
    deadline_to: Optional[date] = None

    for ent in doc.ents:
        label = ent.label_
        raw_entities.setdefault(label, []).append(ent.text)

        if label == "DOMAIN" and not extracted_domain:
            ent_lower = ent.text.lower()
            extracted_domain = _DOMAIN_CANONICAL.get(ent_lower, ent_lower)

        elif label == "OPPORTUNITY_TYPE" and not extracted_type:
            ent_lower = ent.text.lower()
            # Canonicalize hackathon / internship / workshop etc.
            if "hack" in ent_lower:
                extracted_type = "hackathon"
            elif "intern" in ent_lower:
                extracted_type = "internship"
            elif "workshop" in ent_lower or "bootcamp" in ent_lower:
                extracted_type = "workshop"
            elif "competition" in ent_lower or "contest" in ent_lower or "challenge" in ent_lower:
                extracted_type = "competition"
            elif "fellowship" in ent_lower or "scholarship" in ent_lower:
                extracted_type = "fellowship"
            elif "grant" in ent_lower:
                extracted_type = "grant"
            else:
                extracted_type = ent_lower

        elif (label == "LOCATION" or label in ("GPE", "LOC")) and not extracted_location:
            extracted_location = ent.text.strip()

        elif label == "STUDENT_TYPE" and not extracted_dept:
            extracted_dept = ent.text.strip()

        elif label == "TIME_CONSTRAINT" and not deadline_to:
            d_start, d_end = parse_time_constraint(ent.text, ref_date)
            deadline_from, deadline_to = d_start, d_end

        elif label == "DATE" and not deadline_to:
            d_start, d_end = parse_time_constraint(ent.text, ref_date)
            if d_start and d_end:
                deadline_from, deadline_to = d_start, d_end

    # Fallback regex checks for common time phrases if not caught by spaCy
    if not deadline_to:
        for phrase in ["this month", "next month", "this week", "next week", "in 2 weeks", "in two weeks", "upcoming"]:
            if phrase in query.lower():
                deadline_from, deadline_to = parse_time_constraint(phrase, ref_date)
                raw_entities.setdefault("TIME_CONSTRAINT", []).append(phrase)
                break

    # Calculate confidence score
    confidence = 0.0
    if extracted_domain:
        confidence += 0.35
    if extracted_type:
        confidence += 0.25
    if extracted_location:
        confidence += 0.25
    if deadline_to:
        confidence += 0.25
    if extracted_dept:
        confidence += 0.15

    confidence = min(1.0, round(confidence, 2))

    filters = ExtractedFilters(
        domain=extracted_domain,
        location=extracted_location,
        department=extracted_dept,
        opportunity_type=extracted_type,
        deadline_from=deadline_from,
        deadline_to=deadline_to,
        raw_entities=raw_entities,
    )

    return filters, confidence


# ── Core Smart Search Service ─────────────────────────────────────────────────

async def smart_search(
    query: str,
    top_k: int = 10,
    ref_date: Optional[date] = None,
) -> SmartSearchResponse:
    """
    Executes natural language opportunity search:
      1. Extracts entities via spaCy EntityRuler (domain, location, dept, time constraints).
      2. If confidence >= 0.5:
           Executes structured Supabase query:
             domain ILIKE, location ILIKE, deadline BETWEEN, type ILIKE.
      3. If confidence < 0.5 or structured query returns 0 results:
           Falls back to pgvector semantic similarity search using query embeddings.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        raise ValueError("Query string cannot be empty.")

    filters, confidence = extract_search_entities(cleaned_query, ref_date=ref_date)
    logger.info(f"Smart search query='{cleaned_query}', confidence={confidence}, filters={filters}")

    # ── Path A: Structured Query Execution ────────────────────────────────────
    if confidence >= CONFIDENCE_THRESHOLD:
        structured_matches = await _execute_structured_query(filters, top_k=top_k)
        if structured_matches:
            return SmartSearchResponse(
                query=cleaned_query,
                search_mode="structured_filter",
                confidence_score=confidence,
                filters_applied=filters,
                total=len(structured_matches),
                results=structured_matches,
            )
        logger.info("Structured query returned 0 results. Falling back to pgvector semantic search.")

    # ── Path B: pgvector Semantic Search Fallback ──────────────────────────────
    semantic_matches = await _execute_semantic_search(cleaned_query, top_k=top_k)
    search_mode = "semantic_fallback" if confidence < CONFIDENCE_THRESHOLD else "hybrid"

    return SmartSearchResponse(
        query=cleaned_query,
        search_mode=search_mode,
        confidence_score=confidence,
        filters_applied=filters,
        total=len(semantic_matches),
        results=semantic_matches,
    )


# ── Helper: Structured Filter Query ───────────────────────────────────────────

async def _execute_structured_query(
    filters: ExtractedFilters,
    top_k: int = 10,
) -> List[DiscoveredOpportunityItem]:
    """
    Builds and runs structured filters against the `opportunities` Supabase table:
      - domain ILIKE %domain%
      - location ILIKE %location%
      - deadline BETWEEN %start% AND %end%
      - type ILIKE %type%
    """
    query_builder = (
        supabase_admin.table("opportunities")
        .select("id, title, description, domain, type, location, organizer, deadline, is_active")
        .eq("is_active", True)
    )

    if filters.domain:
        query_builder = query_builder.eq("domain", filters.domain.lower())

    if filters.opportunity_type:
        query_builder = query_builder.eq("type", filters.opportunity_type.lower())

    if filters.location:
        query_builder = query_builder.ilike("location", f"%{filters.location}%")

    if filters.deadline_from:
        query_builder = query_builder.gte("deadline", str(filters.deadline_from))

    if filters.deadline_to:
        query_builder = query_builder.lte("deadline", str(filters.deadline_to))

    try:
        resp = query_builder.limit(top_k).execute()
        rows = resp.data or []
    except Exception as exc:
        logger.warning(f"Structured filter query failed ({exc}).")
        return []

    if not rows:
        return []

    # Fetch trust scores in bulk
    opp_ids = [r["id"] for r in rows]
    trust_map = await _get_trust_scores_map(opp_ids)

    results: List[DiscoveredOpportunityItem] = []
    for r in rows:
        trust = trust_map.get(r["id"], 0)
        reasons = []
        if filters.domain and filters.domain.lower() in str(r.get("domain", "")).lower():
            reasons.append(f"Domain: {r.get('domain')}")
        if filters.opportunity_type and filters.opportunity_type.lower() in str(r.get("type", "")).lower():
            reasons.append(f"Type: {r.get('type')}")
        if filters.location and filters.location.lower() in str(r.get("location", "")).lower():
            reasons.append(f"Location: {r.get('location')}")
        if filters.deadline_to and r.get("deadline"):
            reasons.append(f"Deadline: {r.get('deadline')}")

        match_reason = (
            "Matched structured filters (" + ", ".join(reasons) + ")"
            if reasons
            else "Matched structured opportunity criteria"
        )

        results.append(
            DiscoveredOpportunityItem(
                id=UUID(r["id"]),
                title=r.get("title", ""),
                description=r.get("description", ""),
                domain=r.get("domain"),
                type=r.get("type"),
                location=r.get("location"),
                organizer=r.get("organizer"),
                deadline=str(r.get("deadline")) if r.get("deadline") else None,
                trust_score=trust,
                relevance_score=1.0,  # Exact filter match
                match_reason=match_reason,
            )
        )

    return results


# ── Helper: pgvector Semantic Search Fallback ─────────────────────────────────

async def _execute_semantic_search(
    query_text: str,
    top_k: int = 10,
) -> List[DiscoveredOpportunityItem]:
    """
    Fallback semantic search:
      1. Embed raw query using 384-dim SentenceTransformers (all-MiniLM-L6-v2).
      2. Call pgvector RPC `match_opportunities` or perform in-memory cosine ranking.
    """
    embedder = get_local_embedder()
    query_vector = await embedder.embed(query_text)

    # Attempt Supabase RPC match_opportunities (from V009)
    try:
        rpc_resp = supabase_admin.rpc(
            "match_opportunities",
            {
                "query_embedding": query_vector,
                "top_k": top_k,
                "min_score": 0.0,
            },
        ).execute()
        rpc_data = rpc_resp.data or []
        if rpc_data:
            return [
                DiscoveredOpportunityItem(
                    id=UUID(row["id"]),
                    title=row.get("title", ""),
                    description=row.get("description", ""),
                    domain=row.get("domain"),
                    type=row.get("type"),
                    location=row.get("location"),
                    organizer=row.get("organizer"),
                    deadline=str(row.get("deadline")) if row.get("deadline") else None,
                    trust_score=int(row.get("trust_score") or 0),
                    relevance_score=round(float(row.get("similarity", 0.0)), 4),
                    match_reason=(
                        f"Semantic match ({round(float(row.get('similarity', 0.0)) * 100, 1)}% cosine similarity) "
                        f"for '{query_text[:40]}'"
                    ),
                )
                for row in rpc_data
            ]
    except Exception as rpc_exc:
        logger.debug(f"RPC match_opportunities not available ({rpc_exc}). Using query fallback.")

    # In-memory vector fallback
    try:
        opps_resp = (
            supabase_admin.table("opportunities")
            .select("id, title, description, domain, type, location, organizer, deadline, embedding")
            .eq("is_active", True)
            .execute()
        )
        opps = opps_resp.data or []
    except Exception as fetch_exc:
        logger.warning(f"Could not fetch opportunities for semantic fallback: {fetch_exc}")
        return []

    if not opps:
        return []

    opp_ids = [o["id"] for o in opps]
    trust_map = await _get_trust_scores_map(opp_ids)

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for opp in opps:
        emb = opp.get("embedding")
        if emb:
            if isinstance(emb, str):
                try:
                    import json
                    emb = json.loads(emb) if emb.startswith("[") else [float(x.strip()) for x in emb.split(",") if x.strip()]
                except Exception:
                    emb = None
        if emb:
            sim = embedder.cosine_similarity(query_vector, emb)
            scored.append((float(sim), opp))
        else:
            scored.append((0.1, opp))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_scored = scored[:top_k]

    return [
        DiscoveredOpportunityItem(
            id=UUID(opp["id"]),
            title=opp.get("title", ""),
            description=opp.get("description", ""),
            domain=opp.get("domain"),
            type=opp.get("type"),
            location=opp.get("location"),
            organizer=opp.get("organizer"),
            deadline=str(opp.get("deadline")) if opp.get("deadline") else None,
            trust_score=trust_map.get(opp["id"], 0),
            relevance_score=round(sim, 4),
            match_reason=(
                f"Semantic match ({round(sim * 100, 1)}% similarity) for '{query_text[:40]}'"
            ),
        )
        for sim, opp in top_scored
    ]


# ── Helper: Trust Scores Map ──────────────────────────────────────────────────

async def _get_trust_scores_map(opp_ids: List[str]) -> Dict[str, int]:
    """Fetches trust scores for a list of opportunity IDs."""
    if not opp_ids:
        return {}
    try:
        resp = (
            supabase_admin.table("trust_scores")
            .select("opportunity_id, score")
            .in_("opportunity_id", opp_ids)
            .execute()
        )
        return {r["opportunity_id"]: int(r.get("score") or 0) for r in (resp.data or [])}
    except Exception as exc:
        logger.debug(f"Could not fetch trust scores ({exc}). Returning empty map.")
        return {}
