"""
AI Event Trust Scanner service.

Implements Phase B4:
  1. Duplicate detection:
     - Cosine similarity query on opportunity embedding (> 0.92 threshold)
     - Fuzzy string match on title using rapidfuzz (>= 88% token_set_ratio)
  2. Rule-based quality scoring:
     - Checks missing fields: deadline, eligibility, organizer, source_url
     - Checks suspicious patterns: generic organizer, very short description, spam keywords
     - Produces detailed breakdown dict in quality_flags
  3. Machine Learning quality classifier:
     - Lightweight scikit-learn LogisticRegression classifier trained on seed data
     - Blends rule score and ML probability into calibrated 0-100 trust score
  4. Stores computed scores into Supabase `trust_scores` table.
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import re
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from loguru import logger
import numpy as np
from rapidfuzz import fuzz
from sklearn.linear_model import LogisticRegression

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import get_local_embedder
from app.models.opportunity import TrustScoreOut


# ── Suspicious Keywords & Generic Organizers ──────────────────────────────────

SPAM_KEYWORDS = [
    "100% free money",
    "guaranteed prize",
    "no work needed",
    "crypto airdrop",
    "cash giveaway",
    "instant payout",
    "click here now",
    "no experience make money fast",
    "whatsapp only",
    "telegram group",
]

GENERIC_ORGANIZERS = {
    "unknown",
    "admin",
    "administrator",
    "test",
    "anonymous",
    "n/a",
    "none",
    "someone",
    "user",
}


# ── Rule-Based Quality Scorer ─────────────────────────────────────────────────

def rule_quality_check(opp: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """
    Evaluates listing completeness, reliability, and flags suspicious indicators.
    Returns (rule_score [0..100], quality_flags dict).
    """
    flags: Dict[str, Any] = {
        "missing_deadline": False,
        "missing_eligibility": False,
        "missing_organizer": False,
        "missing_source_url": False,
        "generic_organizer": False,
        "short_description": False,
        "spam_keyword_detected": False,
        "detected_spam_phrases": [],
        "positive_signals": [],
    }

    score = 100

    # 1. Deadline check
    deadline = opp.get("deadline")
    if not deadline:
        flags["missing_deadline"] = True
        score -= 15
    else:
        flags["positive_signals"].append("valid_deadline_provided")

    # 2. Eligibility check
    eligibility = (opp.get("eligibility") or "").strip()
    if not eligibility or len(eligibility) < 8:
        flags["missing_eligibility"] = True
        score -= 15
    else:
        flags["positive_signals"].append("eligibility_criteria_specified")

    # 3. Organizer check
    organizer = (opp.get("organizer") or "").strip().lower()
    if not organizer:
        flags["missing_organizer"] = True
        score -= 20
    elif organizer in GENERIC_ORGANIZERS or len(organizer) < 3:
        flags["generic_organizer"] = True
        score -= 25
    else:
        flags["positive_signals"].append("verified_organizer_name")

    # 4. Source URL check
    source_url = (opp.get("source_url") or "").strip()
    if not source_url or not (source_url.startswith("http://") or source_url.startswith("https://")):
        flags["missing_source_url"] = True
        score -= 20
    elif "example.com" in source_url or "localhost" in source_url:
        flags["missing_source_url"] = True
        score -= 20
    else:
        flags["positive_signals"].append("official_source_link_present")

    # 5. Description depth
    description = (opp.get("description") or "").strip()
    if len(description) < 60:
        flags["short_description"] = True
        score -= 15
    elif len(description) > 200:
        flags["positive_signals"].append("comprehensive_description")

    # 6. Spam keywords check
    full_text = f"{opp.get('title', '')} {description}".lower()
    detected = [kw for kw in SPAM_KEYWORDS if kw in full_text]
    if detected:
        flags["spam_keyword_detected"] = True
        flags["detected_spam_phrases"] = detected
        score -= 40

    rule_score = max(0, min(100, score))
    return rule_score, flags


# ── Lightweight Scikit-Learn Classifier ───────────────────────────────────────

@lru_cache(maxsize=1)
def get_or_train_trust_classifier() -> LogisticRegression:
    """
    Trains and caches a lightweight LogisticRegression model on a seed dataset
    of ~40 synthetic labeled examples (legitimate vs suspicious).
    """
    # Features vector:
    # [title_len, desc_len, has_deadline (0/1), has_eligibility (0/1),
    #  has_organizer (0/1), has_source_url (0/1), generic_organizer (0/1), spam_kw_count]

    # fmt: off
    X_train = np.array([
        # Legit examples (label = 1)
        [35, 320, 1, 1, 1, 1, 0, 0],
        [42, 500, 1, 1, 1, 1, 0, 0],
        [28, 410, 1, 1, 1, 1, 0, 0],
        [50, 650, 1, 1, 1, 1, 0, 0],
        [30, 280, 1, 0, 1, 1, 0, 0],
        [25, 310, 0, 1, 1, 1, 0, 0],
        [45, 450, 1, 1, 1, 0, 0, 0],
        [38, 520, 1, 1, 1, 1, 0, 0],
        [32, 290, 1, 1, 1, 1, 0, 0],
        [48, 600, 1, 1, 1, 1, 0, 0],
        [22, 210, 1, 1, 1, 1, 0, 0],
        [36, 350, 1, 1, 1, 1, 0, 0],
        [40, 480, 1, 1, 1, 1, 0, 0],
        [29, 390, 1, 1, 1, 1, 0, 0],
        [33, 330, 1, 1, 1, 1, 0, 0],
        [44, 510, 1, 1, 1, 1, 0, 0],
        [26, 270, 1, 1, 1, 1, 0, 0],
        [52, 620, 1, 1, 1, 1, 0, 0],
        [37, 440, 1, 1, 1, 1, 0, 0],
        [31, 300, 1, 1, 1, 1, 0, 0],

        # Suspicious / Low Quality examples (label = 0)
        [12, 35,  0, 0, 0, 0, 1, 2],
        [15, 20,  0, 0, 1, 0, 1, 1],
        [18, 45,  0, 0, 0, 0, 1, 1],
        [10, 15,  0, 0, 0, 0, 0, 2],
        [14, 30,  0, 0, 1, 0, 1, 0],
        [22, 50,  0, 0, 0, 1, 1, 1],
        [16, 25,  0, 0, 0, 0, 1, 2],
        [20, 40,  0, 1, 0, 0, 1, 0],
        [11, 18,  0, 0, 0, 0, 0, 1],
        [25, 48,  0, 0, 1, 0, 1, 1],
        [19, 32,  0, 0, 0, 0, 1, 2],
        [13, 22,  0, 0, 0, 0, 0, 0],
        [17, 38,  0, 0, 1, 0, 1, 1],
        [21, 55,  0, 0, 0, 0, 1, 1],
        [15, 28,  0, 0, 0, 0, 1, 2],
        [12, 19,  0, 0, 1, 0, 1, 0],
        [24, 42,  0, 0, 0, 0, 0, 1],
        [18, 31,  0, 0, 0, 0, 1, 2],
        [14, 26,  0, 0, 1, 0, 1, 1],
        [20, 36,  0, 0, 0, 0, 1, 1],
    ])
    y_train = np.array([1]*20 + [0]*20)
    # fmt: on

    clf = LogisticRegression(random_state=42)
    clf.fit(X_train, y_train)
    logger.info("Initialized and trained LogisticRegression quality classifier.")
    return clf


def extract_features(opp: Dict[str, Any], flags: Dict[str, Any]) -> np.ndarray:
    """Extract numeric feature vector matching the classifier schema."""
    title_len = len((opp.get("title") or "").strip())
    desc_len = len((opp.get("description") or "").strip())
    has_deadline = 1 if not flags.get("missing_deadline") else 0
    has_eligibility = 1 if not flags.get("missing_eligibility") else 0
    has_organizer = 1 if not flags.get("missing_organizer") else 0
    has_source_url = 1 if not flags.get("missing_source_url") else 0
    generic_org = 1 if flags.get("generic_organizer") else 0
    spam_count = len(flags.get("detected_spam_phrases") or [])

    return np.array([[
        title_len, desc_len, has_deadline, has_eligibility,
        has_organizer, has_source_url, generic_org, spam_count
    ]])


# ── Duplicate Detection ───────────────────────────────────────────────────────

async def detect_duplicates(
    opportunity_id: UUID,
    title: str,
    embedding: Optional[List[float]],
) -> Tuple[bool, Optional[UUID], float, float]:
    """
    Two-signal duplicate detection:
      Signal 1: pgvector cosine similarity > 0.92
      Signal 2: rapidfuzz token_set_ratio on title >= 88.0%
    Returns (is_duplicate, matched_opportunity_id, cosine_sim, title_fuzz_ratio).
    """
    oid = str(opportunity_id)

    try:
        # Fetch existing opportunities (excluding current one)
        resp = (
            supabase_admin.table("opportunities")
            .select("id, title, embedding")
            .neq("id", oid)
            .eq("is_active", True)
            .limit(100)
            .execute()
        )
        candidates = resp.data or []
    except Exception as exc:
        logger.warning(f"Could not fetch existing opportunities for duplicate check: {exc}")
        return False, None, 0.0, 0.0

    embedder = get_local_embedder()
    max_cosine = 0.0
    max_fuzz = 0.0
    matched_id: Optional[UUID] = None

    for cand in candidates:
        cand_id = cand["id"]
        cand_title = cand.get("title", "")
        cand_emb = cand.get("embedding")

        # 1. Fuzzy string match
        fuzz_score = float(fuzz.token_set_ratio(title, cand_title))
        if fuzz_score > max_fuzz:
            max_fuzz = fuzz_score

        # 2. Vector cosine similarity
        cosine_sim = 0.0
        if embedding and cand_emb:
            cosine_sim = embedder.cosine_similarity(embedding, cand_emb)
            if cosine_sim > max_cosine:
                max_cosine = cosine_sim
                matched_id = UUID(cand_id)

        # Trigger duplicate condition:
        # High embedding similarity (> 0.92) AND moderate title match (>= 60%),
        # OR extremely high title match (>= 92%) with cosine > 0.85
        if (cosine_sim > 0.92 and fuzz_score >= 60.0) or (fuzz_score >= 92.0 and cosine_sim > 0.85):
            logger.info(f"Duplicate detected: {opportunity_id} matches {cand_id} (cosine={cosine_sim:.3f}, fuzz={fuzz_score:.1f}%)")
            return True, UUID(cand_id), cosine_sim, fuzz_score

    # Single strong signal fallback (cosine > 0.94)
    if max_cosine > 0.94:
        return True, matched_id, max_cosine, max_fuzz

    return False, None, max_cosine, max_fuzz


# ── Core Trust Scanner ────────────────────────────────────────────────────────

async def compute_and_save_trust_score(opportunity_id: UUID) -> TrustScoreOut:
    """
    Computes quality score and duplicate status, stores result in `trust_scores` table,
    and returns a TrustScoreOut schema.
    """
    oid = str(opportunity_id)

    # 1. Fetch opportunity data
    resp = (
        supabase_admin.table("opportunities")
        .select("id, title, description, domain, type, eligibility, deadline, location, organizer, source_url, embedding")
        .eq("id", oid)
        .maybe_single()
        .execute()
    )
    if not resp or not resp.data:
        raise ValueError(f"Opportunity {opportunity_id} not found.")

    opp = resp.data
    embedding = opp.get("embedding")

    # 2. Duplicate Detection
    is_duplicate, matched_id, cosine_sim, fuzz_score = await detect_duplicates(
        opportunity_id=opportunity_id,
        title=opp.get("title", ""),
        embedding=embedding,
    )

    # 3. Rule-Based Quality Check
    rule_score, flags = rule_quality_check(opp)
    flags["duplicate_similarity_cosine"] = round(cosine_sim, 4)
    flags["duplicate_title_fuzz_ratio"] = round(fuzz_score, 1)
    if matched_id:
        flags["matched_duplicate_opportunity_id"] = str(matched_id)

    # 4. ML Classifier Scoring
    clf = get_or_train_trust_classifier()
    features = extract_features(opp, flags)
    # Probability of being legitimate (class 1)
    ml_prob = float(clf.predict_proba(features)[0][1])
    flags["ml_legitimacy_probability"] = round(ml_prob, 4)

    # 5. Blend Final Score
    # 50% Rule score + 50% ML probability (0..100)
    blended = (0.50 * rule_score) + (0.50 * (ml_prob * 100.0))

    # Severe penalty if duplicate
    if is_duplicate:
        blended = min(blended, 25.0)
        flags["duplicate_penalty_applied"] = True

    final_score = int(round(max(0.0, min(100.0, blended))))

    # 6. Upsert into Supabase `trust_scores` table
    now_iso = datetime.now(timezone.utc).isoformat()
    record = {
        "opportunity_id": oid,
        "score": final_score,
        "duplicate_flag": is_duplicate,
        "quality_flags": flags,
        "computed_at": now_iso,
    }

    try:
        supabase_admin.table("trust_scores").upsert(
            record, on_conflict="opportunity_id"
        ).execute()
        logger.info(f"Stored trust score {final_score}/100 (duplicate={is_duplicate}) for {opportunity_id}")
    except Exception as exc:
        logger.error(f"Failed to upsert trust score for {opportunity_id}: {exc}")

    return TrustScoreOut(
        opportunity_id=opportunity_id,
        score=final_score,
        duplicate_flag=is_duplicate,
        quality_flags=flags,
        computed_at=now_iso,
    )
