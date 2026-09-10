"""
Shared / base Pydantic models used across the application.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DataT = TypeVar("DataT")


# ── Generic API response wrapper ───────────────────────────────────────────────
class APIResponse(BaseModel, Generic[DataT]):
    """Standard envelope for all API responses."""

    success: bool = True
    message: str = "OK"
    data: Optional[DataT] = None
    errors: Optional[List[str]] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ── Pagination ─────────────────────────────────────────────────────────────────
class PaginationMeta(BaseModel):
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
    total: int = 0
    total_pages: int = 0


class PaginatedResponse(APIResponse[List[DataT]], Generic[DataT]):
    pagination: Optional[PaginationMeta] = None


# ── Timestamped base ───────────────────────────────────────────────────────────
class TimestampedModel(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
