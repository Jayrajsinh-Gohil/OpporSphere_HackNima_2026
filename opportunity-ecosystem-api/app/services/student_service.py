"""
Student service — profile CRUD backed by Supabase `students` table.
"""

from __future__ import annotations

from uuid import UUID

from loguru import logger

from app.core.supabase_client import supabase_admin
from app.models.student import StudentCreate, StudentProfile, StudentUpdate
from app.services.match import embed_and_store_student


async def get_profile(student_id: UUID) -> StudentProfile | None:
    """Fetch a student profile by ID."""
    resp = (
        supabase_admin.table("students")
        .select("*")
        .eq("id", str(student_id))
        .maybe_single()
        .execute()
    )
    if not resp.data:
        return None
    return StudentProfile(**resp.data)


async def create_or_update_profile(
    student_id: UUID,
    email: str,
    data: StudentCreate,
) -> StudentProfile:
    """
    Upsert a student profile.
    The `id` always comes from the verified JWT (never from the request body)
    so a user cannot impersonate another student.
    
    Generates and stores 384-dim embedding from skills + interests + career_goals.
    """
    row = data.model_dump(exclude_none=True)
    row["id"] = str(student_id)
    row["email"] = email  # always authoritative from JWT

    resp = (
        supabase_admin.table("students")
        .upsert(row, on_conflict="id")
        .execute()
    )
    if not resp.data:
        raise ValueError("Profile upsert returned no data.")

    logger.info(f"Student profile upserted: {student_id}")

    # Generate & store embedding from concatenated skills+interests+career_goals
    await embed_and_store_student(
        student_id=student_id,
        skills=data.skills,
        interests=data.interests,
        career_goals=data.career_goals,
    )

    return StudentProfile(**resp.data[0])


async def update_profile(
    student_id: UUID,
    data: StudentUpdate,
) -> StudentProfile:
    """Partially update a student profile (PATCH semantics)."""
    updates = data.model_dump(exclude_none=True)
    if not updates:
        raise ValueError("No fields provided for update.")

    resp = (
        supabase_admin.table("students")
        .update(updates)
        .eq("id", str(student_id))
        .execute()
    )
    if not resp.data:
        raise ValueError("Student not found or update failed.")

    logger.info(f"Student profile updated: {student_id}")
    updated_profile = StudentProfile(**resp.data[0])

    # Re-embed if semantic profile text was changed
    embedding_fields = {"skills", "interests", "career_goals"}
    if embedding_fields & updates.keys():
        await embed_and_store_student(
            student_id=student_id,
            skills=updated_profile.skills,
            interests=updated_profile.interests,
            career_goals=updated_profile.career_goals,
        )

    return updated_profile
