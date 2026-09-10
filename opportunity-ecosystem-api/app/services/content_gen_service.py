"""
Content Generation service — AI-powered document drafting.
Generates cover letters, proposals, summaries, cold emails, and bios.
"""

from __future__ import annotations

from app.core.supabase_client import supabase_admin
from app.ml.llm_client import get_llm_client
from app.models.content_gen import ContentGenRequest, ContentGenResponse, ContentType

_PROMPTS: dict[ContentType, str] = {
    ContentType.COVER_LETTER: (
        "Write a compelling cover letter for the opportunity described below. "
        "Highlight how the applicant's skills match the requirements. "
        "Tone: {tone}. Max words: {max_words}.\n\n"
        "Applicant profile:\n{profile}\n\nOpportunity:\n{opportunity}"
    ),
    ContentType.PROPOSAL: (
        "Write a professional project proposal for this opportunity. "
        "Include an approach, timeline sketch, and why this applicant is the right fit. "
        "Tone: {tone}. Max words: {max_words}.\n\n"
        "Applicant profile:\n{profile}\n\nOpportunity:\n{opportunity}"
    ),
    ContentType.SUMMARY: (
        "Summarise the opportunity below in a clear, engaging way for someone considering applying. "
        "Tone: {tone}. Max words: {max_words}.\n\nOpportunity:\n{opportunity}"
    ),
    ContentType.COLD_EMAIL: (
        "Write a personalised cold email to introduce the applicant and express interest "
        "in the opportunity. Be concise and direct. "
        "Tone: {tone}. Max words: {max_words}.\n\n"
        "Applicant profile:\n{profile}\n\nOpportunity:\n{opportunity}"
    ),
    ContentType.BIO: (
        "Write a short professional bio for the applicant suitable for an opportunity application. "
        "Tone: {tone}. Max words: {max_words}.\n\nApplicant profile:\n{profile}"
    ),
}


async def generate_content(request: ContentGenRequest) -> ContentGenResponse:
    """Generate AI content based on user profile and opportunity context."""
    llm = get_llm_client()

    # ── Fetch user profile ─────────────────────────────────────────────────────
    profile_resp = (
        supabase_admin.table("profiles")
        .select("full_name, bio, skills, interests")
        .eq("id", str(request.user_id))
        .single()
        .execute()
    )
    p = profile_resp.data or {}
    profile_text = (
        f"Name: {p.get('full_name', 'Applicant')}\n"
        f"Bio: {p.get('bio', 'Not provided')}\n"
        f"Skills: {', '.join(p.get('skills', []))}\n"
        f"Interests: {', '.join(p.get('interests', []))}"
    )

    # ── Fetch opportunity if provided ──────────────────────────────────────────
    opportunity_text = "Not specified"
    if request.opportunity_id:
        opp_resp = (
            supabase_admin.table("opportunities")
            .select("title, description, required_skills")
            .eq("id", str(request.opportunity_id))
            .single()
            .execute()
        )
        opp = opp_resp.data or {}
        opportunity_text = (
            f"Title: {opp.get('title', '')}\n"
            f"Description: {opp.get('description', '')}\n"
            f"Required skills: {', '.join(opp.get('required_skills', []))}"
        )

    if request.additional_context:
        opportunity_text += f"\n\nAdditional context: {request.additional_context}"

    # ── Build prompt from template ─────────────────────────────────────────────
    template = _PROMPTS[request.content_type]
    prompt = template.format(
        tone=request.tone,
        max_words=request.max_words,
        profile=profile_text,
        opportunity=opportunity_text,
    )

    generated = await llm.chat(
        user_prompt=prompt,
        system_prompt=(
            "You are an expert career coach and professional writer. "
            "Write only the requested document, no meta-commentary."
        ),
        temperature=0.75,
        max_tokens=request.max_words * 2,  # generous token budget
    )

    word_count = len(generated.split())

    return ContentGenResponse(
        content_type=request.content_type,
        generated_text=generated,
        word_count=word_count,
        opportunity_id=request.opportunity_id,
    )
