"""
Content Generation routes — /api/v1/content-gen
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentStudent
from app.models.base import APIResponse
from app.models.content_gen import (
    ContentGenerateRequest,
    ContentGenerateResponse,
    ContentGenRequest,
    ContentGenResponse,
)
from app.services import content_gen, content_gen_service

router = APIRouter(prefix="/content", tags=["Content Generation"])


@router.post(
    "/generate",
    response_model=APIResponse[ContentGenerateResponse],
    summary="Generate content via local Ollama (summary, notification, team_invite, bio)",
    description=(
        "Supports 4 types: "
        "- summary (extracts structured fields + 2-3 sentence summary) "
        "- notification (student + matched opportunity alert) "
        "- team_invite (inviter + shared event + skills) "
        "- bio (one-paragraph profile bio from skills & interests)"
    ),
)
async def generate_ollama_content(
    body: ContentGenerateRequest,
    current_student: CurrentStudent,
):
    try:
        result = await content_gen.generate_content(body)
        return APIResponse(data=result, message="Content generated successfully.")
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {exc}",
        )


@router.post(
    "/",
    response_model=APIResponse[ContentGenResponse],
    summary="Generate AI-drafted content (cover letter, proposal, etc.)",
)
async def generate(
    body: ContentGenRequest,
    current_student: CurrentStudent,
):
    try:
        result = await content_gen_service.generate_content(body)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        )
    return APIResponse(data=result, message="Content generated successfully.")
