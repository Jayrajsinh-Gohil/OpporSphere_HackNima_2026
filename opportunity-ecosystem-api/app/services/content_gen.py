"""
Content Generation service using local Ollama (llama3.2:3b).

Implements Phase B5:
  Four generation types:
    1. summary:
       - Extracts structured fields (domain, eligibility, deadline) via regex patterns first.
       - Uses LLM for a clean 2-3 sentence natural-language summary.
    2. notification:
       - Personalized message using student name + matched opportunity title.
    3. team_invite:
       - Short invite message using inviter name + shared event + shared skills.
    4. bio:
       - Turns a student's raw skills/interests list into a one-paragraph profile bio.
  Keeps prompts short and templated for predictable output.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from app.models.content_gen import (
    ContentGenerateRequest,
    ContentGenerateResponse,
    GenerationType,
)



# ── Structured Fields Extractor (Regex & Heuristics) ──────────────────────────

def extract_structured_fields(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Extracts structured fields (deadline, eligibility, domain) from raw text
    using regular expressions and heuristic keyword patterns.
    """
    structured: Dict[str, Optional[str]] = {
        "deadline": None,
        "eligibility": None,
        "domain": None,
    }

    # 1. Deadline extraction
    # Patterns: "deadline: YYYY-MM-DD", "deadline: Month DD, YYYY", "due by DD/MM/YYYY"
    date_pattern = re.compile(
        r"(?:deadline|due\s+date|apply\s+by|last\s+date)\s*[:\-]?\s*"
        r"([0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}|"
        r"[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{4}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s+[0-9]{4})",
        re.IGNORECASE,
    )
    match_date = date_pattern.search(raw_text)
    if match_date:
        structured["deadline"] = match_date.group(1).strip()
    else:
        # Fallback date pattern
        generic_date = re.search(
            r"\b([0-9]{4}-[0-9]{2}-[0-9]{2})\b|"
            r"\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
            raw_text,
            re.IGNORECASE,
        )
        if generic_date:
            structured["deadline"] = (generic_date.group(1) or generic_date.group(2)).strip()

    # 2. Eligibility extraction
    # Patterns: "eligibility: ...", "eligible: ...", "open to ..."
    eligibility_pattern = re.compile(
        r"(?:eligibility|eligible|open\s+to|who\s+can\s+apply)\s*[:\-]?\s*([^\n\.\;]{10,120})",
        re.IGNORECASE,
    )
    match_elig = eligibility_pattern.search(raw_text)
    if match_elig:
        structured["eligibility"] = match_elig.group(1).strip()
    elif re.search(r"\b(undergraduates?|college students?|high school|graduates?|all students)\b", raw_text, re.IGNORECASE):
        student_match = re.search(r"\b(open to [^,\.\n]+|for (?:all )?(?:undergraduates?|students?))\b", raw_text, re.IGNORECASE)
        structured["eligibility"] = student_match.group(0).strip() if student_match else "Open to enrolled students"
    else:
        structured["eligibility"] = "Open to eligible students and early-career learners"

    # 3. Domain classification
    text_lower = raw_text.lower()
    if any(w in text_lower for w in ["ai", "machine learning", "software", "hackathon", "coding", "algorithm", "developer", "cloud"]):
        structured["domain"] = "technology"
    elif any(w in text_lower for w in ["biology", "chemistry", "physics", "genomics", "clinical", "scientific"]):
        structured["domain"] = "science"
    elif any(w in text_lower for w in ["startup", "pitch", "business", "finance", "venture", "marketing"]):
        structured["domain"] = "business"
    elif any(w in text_lower for w in ["climate", "sustainability", "environment", "clean energy", "green"]):
        structured["domain"] = "environment"
    elif any(w in text_lower for w in ["health", "medical", "medicine", "wellness"]):
        structured["domain"] = "health"
    elif any(w in text_lower for w in ["social impact", "community", "ngo", "education"]):
        structured["domain"] = "social_impact"
    else:
        structured["domain"] = "other"

    return structured


# ── Unified LLM Helper ────────────────────────────────────────────────────────

async def _call_llm(prompt: str, system_prompt: str, max_tokens: int = 250) -> str:
    """Executes prompt via active LLM provider (Gemini or Ollama) with fallback."""
    from app.ml.llm_client import get_llm_client
    try:
        llm = await get_llm_client()
        return await llm.chat(
            user_prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        logger.warning(f"LLM call failed ({exc}). Using template fallback.")
        return ""


# ── Generation Handlers ───────────────────────────────────────────────────────

async def generate_summary(input_data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Generates 2-3 sentence summary + extracted structured fields."""
    raw_text = input_data.get("text") or input_data.get("content") or ""
    if not raw_text:
        raise ValueError("Input 'text' is required for summary generation.")

    # 1. Extract structured fields via regex
    structured = extract_structured_fields(raw_text)

    # 2. Templated prompt for LLM
    system_prompt = (
        "You are an AI opportunity parser. Summarize the opportunity in 2 to 3 concise, compelling sentences. "
        "Highlight the core challenge and potential rewards. Do not add conversational fluff or preambles."
    )
    prompt = f"Opportunity Text:\n{raw_text[:2000]}\n\nSummary (2-3 sentences):"

    generated = await _call_llm(prompt, system_prompt, max_tokens=150)
    if not generated:
        # High quality fallback summary
        first_few = ". ".join([s.strip() for s in raw_text.split(".")[:2] if len(s.strip()) > 15])
        generated = f"{first_few}. This opportunity offers hands-on experience and professional growth for students."

    return generated, structured


async def generate_notification(input_data: Dict[str, Any]) -> str:
    """Personalized notification using student name + matched opportunity title."""
    student_name = input_data.get("student_name") or input_data.get("name") or "Student"
    opp_title = input_data.get("opportunity_title") or input_data.get("title") or "a top-tier opportunity"

    system_prompt = (
        "You write concise push notifications for a student opportunity platform. "
        "Keep the message inspiring, direct, and under 25 words."
    )
    prompt = (
        f"Student Name: {student_name}\n"
        f"Matched Opportunity: {opp_title}\n\n"
        "Notification Message:"
    )

    generated = await _call_llm(prompt, system_prompt, max_tokens=60)
    if not generated:
        generated = f"Hey {student_name}! We found a great match for your profile: {opp_title}. Check it out and apply today!"

    return generated


async def generate_team_invite(input_data: Dict[str, Any]) -> str:
    """Short invite message using inviter name + shared event + shared skills."""
    inviter_name = input_data.get("inviter_name") or "A fellow student"
    event_name = input_data.get("event_name") or input_data.get("opportunity_title") or "the upcoming event"
    shared_skills = input_data.get("shared_skills") or ["teamwork", "coding"]
    if isinstance(shared_skills, list):
        skills_str = ", ".join(shared_skills)
    else:
        skills_str = str(shared_skills)

    system_prompt = (
        "You write short, friendly hackathon/event team invitations. "
        "Keep it enthusiastic, welcoming, and under 35 words."
    )
    prompt = (
        f"Inviter: {inviter_name}\n"
        f"Event: {event_name}\n"
        f"Shared Skills: {skills_str}\n\n"
        "Team Invitation:"
    )

    generated = await _call_llm(prompt, system_prompt, max_tokens=70)
    if not generated:
        generated = f"Hi! {inviter_name} is inviting you to team up for {event_name}. Your shared strengths in {skills_str} would make an unstoppable squad!"

    return generated


async def generate_bio(input_data: Dict[str, Any]) -> str:
    """Turns a student's raw skills/interests list into a one-paragraph profile bio."""
    skills = input_data.get("skills") or []
    interests = input_data.get("interests") or []
    name = input_data.get("name") or "I am"

    skills_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
    interests_str = ", ".join(interests) if isinstance(interests, list) else str(interests)

    system_prompt = (
        "You write concise, professional student bios for hackathons and internships. "
        "Write exactly one cohesive paragraph (40-70 words) showcasing their potential and drive. "
        "Do not use bullet points or intros."
    )
    prompt = (
        f"Skills: {skills_str or 'Software Engineering'}\n"
        f"Interests: {interests_str or 'Technology & Innovation'}\n\n"
        "Professional Bio:"
    )

    generated = await _call_llm(prompt, system_prompt, max_tokens=100)
    if not generated:
        generated = (
            f"Passionate and driven student technologist skilled in {skills_str or 'software development'}, "
            f"with a keen interest in exploring {interests_str or 'emerging technologies'}. "
            f"Eager to collaborate on impactful real-world projects and build innovative solutions."
        )

    return generated


# ── Unified Service Entry Point ───────────────────────────────────────────────

async def generate_content(request: ContentGenerateRequest) -> ContentGenerateResponse:
    """
    Dispatches generation based on request.type:
      - summary
      - notification
      - team_invite
      - bio
    """
    structured_data: Optional[Dict[str, Any]] = None

    if request.type == GenerationType.SUMMARY:
        content, structured_data = await generate_summary(request.input_data)
    elif request.type == GenerationType.NOTIFICATION:
        content = await generate_notification(request.input_data)
    elif request.type == GenerationType.TEAM_INVITE:
        content = await generate_team_invite(request.input_data)
    elif request.type == GenerationType.BIO:
        content = await generate_bio(request.input_data)
    else:
        raise ValueError(f"Unsupported generation type: {request.type}")

    return ContentGenerateResponse(
        type=request.type,
        generated_content=content,
        structured_data=structured_data,
        model=DEFAULT_MODEL,
    )
