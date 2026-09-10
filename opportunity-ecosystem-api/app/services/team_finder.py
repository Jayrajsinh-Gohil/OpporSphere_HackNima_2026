"""
Team Finder service — compatibility matching, role-based teaming, and invitation workflows.

Implements Phase B6:
  1. GET /api/team-finder/matches?event_id=X:
     - Finds other students registered for the same event without a team.
     - Reuses profile embeddings from Phase B3 (SentenceTransformer 384-dim).
     - Calculates cosine similarity and applies bonus weight for complementary roles
       (complementary roles > duplicate roles).
  2. POST /api/team-finder/invite:
     - Creates a `team_members` pending invite.
     - Uses Phase B5 Content Generation's `team_invite` type to draft a personalized invite message.
  3. POST /api/team-finder/teams:
     - Creates a team for an event and adds accepted members.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.ml.embeddings import SentenceTransformerEmbedder, get_local_embedder
from app.models.content_gen import ContentGenerateRequest, GenerationType
from app.models.student import StudentProfile
from app.models.team_finder import (
    TeamCreateRequest,
    TeamInviteRequest,
    TeamInviteResponse,
    TeamMatchesResponse,
    TeamMatchItem,
    TeamMemberOut,
    TeamResponse,
)
from app.services import content_gen
from app.services.match import build_student_embed_text, embed_and_store_student

# Role bonus constant for complementary roles
COMPLEMENTARY_ROLE_BONUS = 0.15


# ── Role Inference & Complementarity Helpers ─────────────────────────────────

_ROLE_KEYWORDS: Dict[str, List[str]] = {
    "Frontend Developer": [
        "react", "vue", "angular", "svelte", "html", "css", "tailwind", "frontend",
        "next.js", "nextjs", "javascript", "typescript", "web development", "ui",
    ],
    "Backend Developer": [
        "node", "express", "django", "fastapi", "flask", "spring", "sql", "postgres",
        "backend", "mongodb", "database", "golang", "java", "api", "redis",
    ],
    "AI/ML Engineer": [
        "ml", "machine learning", "ai", "artificial intelligence", "deep learning",
        "pytorch", "tensorflow", "nlp", "computer vision", "data science", "keras",
        "transformers", "llm", "pandas", "numpy",
    ],
    "UI/UX Designer": [
        "figma", "ui/ux", "ux", "design", "wireframe", "prototyping", "user research",
        "graphic design", "product design",
    ],
    "Mobile Developer": [
        "flutter", "react native", "android", "ios", "swift", "kotlin", "mobile",
    ],
    "DevOps / Cloud Engineer": [
        "docker", "kubernetes", "aws", "gcp", "azure", "ci/cd", "devops", "cloud",
        "linux", "terraform",
    ],
    "Product Manager": [
        "product management", "product manager", "scrum", "agile", "pitch",
        "business", "entrepreneurship", "marketing", "finance", "strategy",
    ],
}


def infer_student_role(student: Dict[str, Any]) -> str:
    """
    Determines student's preferred/primary role:
      1. Uses explicit `preferred_role` if available.
      2. Otherwise infers role by scoring keywords against skills, interests, and career_goals.
      3. Defaults to 'Full Stack Developer' if ambiguous.
    """
    explicit = student.get("preferred_role")
    if explicit and str(explicit).strip():
        return str(explicit).strip()

    skills = [s.lower() for s in (student.get("skills") or []) if s]
    interests = [i.lower() for i in (student.get("interests") or []) if i]
    career_goals = (student.get("career_goals") or "").lower()

    text_blob = " ".join(skills + interests + [career_goals])
    if not text_blob.strip():
        return "Full Stack Developer"

    role_scores: Dict[str, int] = {}
    for role, keywords in _ROLE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text_blob:
                score += 2 if kw in skills else 1
        if score > 0:
            role_scores[role] = score

    if not role_scores:
        return "Full Stack Developer"

    # Return role with highest match score
    best_role = max(role_scores.items(), key=lambda x: x[1])[0]
    return best_role


def is_role_complementary(role_a: str, role_b: str) -> bool:
    """
    Complementary roles differ from each other (e.g. Frontend + Backend, AI/ML + UI/UX).
    Duplicate roles (Frontend + Frontend) receive no bonus.
    """
    clean_a = role_a.strip().lower()
    clean_b = role_b.strip().lower()
    return clean_a != clean_b


# ── Match Finding Service ─────────────────────────────────────────────────────

async def get_team_matches(
    current_student: StudentProfile,
    event_id: UUID,
    preferred_role: Optional[str] = None,
    top_k: int = 10,
) -> TeamMatchesResponse:
    """
    Finds other students registered for the same event who do not already have a team,
    ranked by cosine similarity of skill/interest embeddings with complementary role bonus.
    """
    eid_str = str(event_id)
    sid_str = str(current_student.id)

    # 1. Fetch Event & Opportunity Details
    event_resp = (
        supabase_admin.table("events")
        .select("id, opportunity_id, extra_details, status")
        .eq("id", eid_str)
        .maybe_single()
        .execute()
    )
    if not event_resp or not event_resp.data:
        raise ValueError(f"Event with ID {event_id} not found.")

    event_data = event_resp.data
    opp_id = event_data.get("opportunity_id")

    opp_title = "Event"
    if opp_id:
        opp_resp = (
            supabase_admin.table("opportunities")
            .select("title")
            .eq("id", str(opp_id))
            .maybe_single()
            .execute()
        )
        if opp_resp and opp_resp.data:
            opp_title = opp_resp.data.get("title", "Event")

    # 2. Get current student profile & embedding (reusing Phase B3)
    curr_resp = (
        supabase_admin.table("students")
        .select("id, name, skills, interests, career_goals, embedding")
        .eq("id", sid_str)
        .maybe_single()
        .execute()
    )
    curr_data = curr_resp.data if (curr_resp and curr_resp.data) else {}
    curr_embedding = curr_data.get("embedding")

    if not curr_embedding:
        curr_embedding = await embed_and_store_student(
            current_student.id,
            skills=current_student.skills,
            interests=current_student.interests,
            career_goals=current_student.career_goals,
        )

    # Determine current student role
    my_role = preferred_role or infer_student_role(curr_data or current_student.model_dump())

    # 3. Find students who ALREADY have an accepted team for this event
    # A student has a team if they created a team for this event or are an accepted member
    teams_resp = (
        supabase_admin.table("teams")
        .select("id, created_by")
        .eq("event_id", eid_str)
        .execute()
    )
    teams_in_event = teams_resp.data or []
    team_ids = [t["id"] for t in teams_in_event if t.get("id")]
    team_creators = {t["created_by"] for t in teams_in_event if t.get("created_by")}

    students_with_team: Set[str] = set(team_creators)
    if team_ids:
        members_resp = (
            supabase_admin.table("team_members")
            .select("student_id, status")
            .in_("team_id", team_ids)
            .execute()
        )
        for m in (members_resp.data or []):
            # Exclude accepted members; pending invites do not count as formed teams
            if m.get("status") in (None, "accepted"):
                students_with_team.add(m["student_id"])

    # Excluded set includes students with teams and the current student
    excluded_ids: Set[str] = students_with_team.union({sid_str})

    # 4. Identify students registered for this event
    # Registered students: applied for the event's parent opportunity or in extra_details
    candidate_ids: Set[str] = set()

    if opp_id:
        apps_resp = (
            supabase_admin.table("applications")
            .select("student_id, status")
            .eq("opportunity_id", str(opp_id))
            .execute()
        )
        for app in (apps_resp.data or []):
            if app.get("status") not in ("withdrawn", "rejected"):
                candidate_ids.add(app["student_id"])

    extra_details = event_data.get("extra_details") or {}
    if isinstance(extra_details, dict):
        for reg_id in extra_details.get("registered_student_ids", []):
            candidate_ids.add(str(reg_id))

    # Remove excluded IDs
    eligible_candidate_ids = [cid for cid in candidate_ids if cid not in excluded_ids]

    # Fallback: if no registrations are found in DB (e.g. testing or open registrations),
    # fetch other active students who don't have a team
    if not eligible_candidate_ids:
        all_students_resp = (
            supabase_admin.table("students")
            .select("id")
            .eq("is_active", True)
            .execute()
        )
        eligible_candidate_ids = [
            s["id"] for s in (all_students_resp.data or [])
            if s["id"] not in excluded_ids
        ]

    if not eligible_candidate_ids:
        return TeamMatchesResponse(
            event_id=event_id,
            event_title=opp_title,
            current_student_id=current_student.id,
            current_student_name=current_student.name,
            current_student_role=my_role,
            total_candidates=0,
            matches=[],
        )

    # 5. Fetch candidate student profiles & embeddings
    candidates_resp = (
        supabase_admin.table("students")
        .select("id, name, avatar_url, department, location, skills, interests, career_goals, embedding")
        .in_("id", eligible_candidate_ids)
        .execute()
    )
    candidates: List[Dict[str, Any]] = candidates_resp.data or []

    # 6. Rank candidates by cosine similarity + complementary role bonus
    embedder = get_local_embedder()
    scored_candidates: List[TeamMatchItem] = []

    my_skills_set = {s.lower().strip() for s in (current_student.skills or [])}

    for cand in candidates:
        cand_id = UUID(cand["id"])
        cand_embedding = cand.get("embedding")

        # Auto-compute candidate embedding if missing (Phase B3 reuse)
        if not cand_embedding:
            cand_embedding = await embed_and_store_student(
                cand_id,
                skills=cand.get("skills") or [],
                interests=cand.get("interests") or [],
                career_goals=cand.get("career_goals"),
            )

        # Cosine similarity
        if curr_embedding and cand_embedding:
            sim = embedder.cosine_similarity(curr_embedding, cand_embedding)
            sim = max(0.0, min(1.0, float(sim)))
        else:
            # Fallback text Jaccard similarity if embeddings unavailable
            cand_skills_set = {s.lower().strip() for s in (cand.get("skills") or [])}
            inter = len(my_skills_set.intersection(cand_skills_set))
            union = len(my_skills_set.union(cand_skills_set))
            sim = (inter / union) if union > 0 else 0.3

        # Role inference & complementarity
        cand_role = infer_student_role(cand)
        is_comp = is_role_complementary(my_role, cand_role)
        role_bonus = COMPLEMENTARY_ROLE_BONUS if is_comp else 0.0

        # Weighted final match score (complementary roles strictly favored over duplicate roles)
        # 85% embedding similarity + 15% role complementarity
        final_score = min(1.0, round((sim * 0.85) + role_bonus, 4))
        match_pct = round(final_score * 100.0, 1)

        # Skills overlap & differences
        cand_skills = cand.get("skills") or []
        shared = [s for s in cand_skills if s.lower().strip() in my_skills_set]
        complementary_skills = [s for s in cand_skills if s.lower().strip() not in my_skills_set]

        # Recommendation explanation
        if is_comp:
            reason = (
                f"Complementary role match ({cand_role} + {my_role}) with "
                f"{len(shared)} shared skill{'s' if len(shared) != 1 else ''} and "
                f"{len(complementary_skills)} complementary skill{'s' if len(complementary_skills) != 1 else ''}."
            )
        else:
            reason = (
                f"Shared focus in {cand_role} with strong skill alignment "
                f"({round(sim * 100, 1)}% cosine similarity)."
            )

        scored_candidates.append(
            TeamMatchItem(
                student_id=cand_id,
                name=cand.get("name", "Student"),
                avatar_url=cand.get("avatar_url"),
                department=cand.get("department"),
                skills=cand_skills,
                interests=cand.get("interests") or [],
                preferred_role=cand_role,
                similarity_score=round(sim, 4),
                role_bonus=round(role_bonus, 4),
                match_score=final_score,
                match_percentage=match_pct,
                is_complementary=is_comp,
                shared_skills=shared,
                complementary_skills=complementary_skills,
                recommendation_reason=reason,
            )
        )

    # Sort descending by final match score
    scored_candidates.sort(key=lambda x: x.match_score, reverse=True)
    top_matches = scored_candidates[:top_k]

    return TeamMatchesResponse(
        event_id=event_id,
        event_title=opp_title,
        current_student_id=current_student.id,
        current_student_name=current_student.name,
        current_student_role=my_role,
        total_candidates=len(scored_candidates),
        matches=top_matches,
    )


# ── Team Invite Service ───────────────────────────────────────────────────────

async def create_team_invite(
    current_student: StudentProfile,
    request: TeamInviteRequest,
) -> TeamInviteResponse:
    """
    Creates a pending `team_members` invite row.
    Uses Phase B5 Content Generation's `team_invite` type to draft the invite message.
    """
    eid_str = str(request.event_id)
    inviter_id_str = str(current_student.id)
    invited_id_str = str(request.invited_student_id)

    if inviter_id_str == invited_id_str:
        raise ValueError("Cannot send a team invite to yourself.")

    # 1. Fetch invited student
    invited_resp = (
        supabase_admin.table("students")
        .select("id, name, skills")
        .eq("id", invited_id_str)
        .maybe_single()
        .execute()
    )
    if not invited_resp or not invited_resp.data:
        raise ValueError(f"Student {request.invited_student_id} does not exist.")

    invited_student = invited_resp.data
    invited_name = invited_student.get("name", "Fellow Student")

    # 2. Fetch event & opportunity title
    event_resp = (
        supabase_admin.table("events")
        .select("id, opportunity_id")
        .eq("id", eid_str)
        .maybe_single()
        .execute()
    )
    if not event_resp or not event_resp.data:
        raise ValueError(f"Event {request.event_id} not found.")

    opp_title = "Upcoming Event"
    opp_id = event_resp.data.get("opportunity_id")
    if opp_id:
        opp_resp = (
            supabase_admin.table("opportunities")
            .select("title")
            .eq("id", str(opp_id))
            .maybe_single()
            .execute()
        )
        if opp_resp and opp_resp.data:
            opp_title = opp_resp.data.get("title", opp_title)

    # 3. Locate or create team for the inviter in this event
    team_id: UUID
    team_name: str

    if request.team_id:
        team_resp = (
            supabase_admin.table("teams")
            .select("id, name, event_id, created_by")
            .eq("id", str(request.team_id))
            .maybe_single()
            .execute()
        )
        if not team_resp or not team_resp.data:
            raise ValueError(f"Team {request.team_id} does not exist.")
        team = team_resp.data
        if team.get("event_id") != eid_str:
            raise ValueError(f"Team {request.team_id} does not belong to event {request.event_id}.")
        team_id = UUID(team["id"])
        team_name = team["name"]
    else:
        # Check if current student already created a team for this event
        existing_team_resp = (
            supabase_admin.table("teams")
            .select("id, name")
            .eq("event_id", eid_str)
            .eq("created_by", inviter_id_str)
            .maybe_single()
            .execute()
        )
        if existing_team_resp and existing_team_resp.data:
            team_id = UUID(existing_team_resp.data["id"])
            team_name = existing_team_resp.data["name"]
        else:
            # Create a team for the inviter
            new_team_id = uuid4()
            team_name = f"{current_student.name}'s Squad"
            supabase_admin.table("teams").insert({
                "id": str(new_team_id),
                "event_id": eid_str,
                "name": team_name,
                "created_by": inviter_id_str,
                "is_open": True,
            }).execute()

            # Add creator as leader
            try:
                supabase_admin.table("team_members").insert({
                    "team_id": str(new_team_id),
                    "student_id": inviter_id_str,
                    "role": "leader",
                    "status": "accepted",
                }).execute()
            except Exception as exc:
                logger.warning(f"Error adding creator to team_members (handled): {exc}")

            team_id = new_team_id

    # 4. Draft invite message using Phase B5 Content Generation's team_invite type
    my_skills = set(s.lower().strip() for s in (current_student.skills or []))
    cand_skills = set(s.lower().strip() for s in (invited_student.get("skills") or []))
    shared_skills = list(my_skills.intersection(cand_skills))
    if not shared_skills:
        shared_skills = current_student.skills[:2] if current_student.skills else ["collaboration", "coding"]

    draft_response = await content_gen.generate_content(
        ContentGenerateRequest(
            type=GenerationType.TEAM_INVITE,
            input_data={
                "inviter_name": current_student.name,
                "event_name": opp_title,
                "shared_skills": shared_skills,
            },
        )
    )
    ai_drafted_message = draft_response.generated_content

    final_message = (
        f"{request.custom_message.strip()} — {ai_drafted_message}"
        if request.custom_message and request.custom_message.strip()
        else ai_drafted_message
    )

    # 5. Insert / Upsert pending invite into team_members
    invite_id = uuid4()
    member_record = {
        "id": str(invite_id),
        "team_id": str(team_id),
        "student_id": invited_id_str,
        "role": request.role or "member",
        "status": "pending",
        "invite_message": final_message,
    }

    try:
        supabase_admin.table("team_members").upsert(
            member_record, on_conflict="team_id,student_id"
        ).execute()
    except Exception as exc:
        logger.warning(f"Failed upsert on team_members with full fields ({exc}). Retrying standard fields.")
        # Fallback if status/invite_message columns are pending migration
        supabase_admin.table("team_members").upsert(
            {
                "id": str(invite_id),
                "team_id": str(team_id),
                "student_id": invited_id_str,
                "role": request.role or "member",
            },
            on_conflict="team_id,student_id",
        ).execute()

    return TeamInviteResponse(
        invite_id=invite_id,
        team_id=team_id,
        team_name=team_name,
        event_id=request.event_id,
        inviter_id=current_student.id,
        inviter_name=current_student.name,
        invited_student_id=request.invited_student_id,
        invited_student_name=invited_name,
        role=request.role or "member",
        status="pending",
        message=final_message,
        created_at=datetime.now(timezone.utc),
    )


# ── Team Creation Service ─────────────────────────────────────────────────────

async def create_team_with_members(
    current_student: StudentProfile,
    request: TeamCreateRequest,
) -> TeamResponse:
    """
    Creates a team for a specific event and adds accepted members.
    Creator is automatically assigned as 'leader'.
    """
    eid_str = str(request.event_id)
    creator_id_str = str(current_student.id)

    # 1. Validate event existence
    event_resp = (
        supabase_admin.table("events")
        .select("id")
        .eq("id", eid_str)
        .maybe_single()
        .execute()
    )
    if not event_resp or not event_resp.data:
        raise ValueError(f"Event {request.event_id} not found.")

    # 2. Check for existing team created by this student for the same event (uq_teams_event_creator)
    existing_resp = (
        supabase_admin.table("teams")
        .select("id")
        .eq("event_id", eid_str)
        .eq("created_by", creator_id_str)
        .maybe_single()
        .execute()
    )
    if existing_resp and existing_resp.data:
        raise ValueError(f"You have already created a team for this event (Team ID: {existing_resp.data['id']}).")

    # 3. Create the team
    team_id = uuid4()
    now_dt = datetime.now(timezone.utc)

    team_row = {
        "id": str(team_id),
        "event_id": eid_str,
        "name": request.name.strip(),
        "created_by": creator_id_str,
        "is_open": request.is_open,
    }
    supabase_admin.table("teams").insert(team_row).execute()

    # 4. Add creator as team leader
    members_to_insert = [
        {
            "id": str(uuid4()),
            "team_id": str(team_id),
            "student_id": creator_id_str,
            "role": "leader",
            "status": "accepted",
        }
    ]

    # 5. Add accepted members from member_ids
    for mid in request.member_ids:
        mid_str = str(mid)
        if mid_str != creator_id_str:
            members_to_insert.append({
                "id": str(uuid4()),
                "team_id": str(team_id),
                "student_id": mid_str,
                "role": "member",
                "status": "accepted",
            })

    try:
        supabase_admin.table("team_members").upsert(
            members_to_insert, on_conflict="team_id,student_id"
        ).execute()
    except Exception as exc:
        logger.warning(f"Failed upsert on team_members with full fields ({exc}). Fallback to standard insert.")
        standard_members = [
            {
                "id": m["id"],
                "team_id": m["team_id"],
                "student_id": m["student_id"],
                "role": m["role"],
            }
            for m in members_to_insert
        ]
        supabase_admin.table("team_members").upsert(
            standard_members, on_conflict="team_id,student_id"
        ).execute()

    # 6. Fetch member profiles for rich response
    all_member_ids = [m["student_id"] for m in members_to_insert]
    students_resp = (
        supabase_admin.table("students")
        .select("id, name, avatar_url")
        .in_("id", all_member_ids)
        .execute()
    )
    student_map = {s["id"]: s for s in (students_resp.data or [])}

    output_members: List[TeamMemberOut] = []
    for m in members_to_insert:
        s_info = student_map.get(m["student_id"]) or {}
        output_members.append(
            TeamMemberOut(
                student_id=UUID(m["student_id"]),
                name=s_info.get("name", current_student.name if m["student_id"] == creator_id_str else "Member"),
                role=m["role"],
                status=m.get("status", "accepted"),
                avatar_url=s_info.get("avatar_url"),
                joined_at=now_dt,
            )
        )

    return TeamResponse(
        id=team_id,
        event_id=request.event_id,
        name=request.name.strip(),
        created_by=current_student.id,
        is_open=request.is_open,
        members=output_members,
        created_at=now_dt,
        updated_at=now_dt,
    )
