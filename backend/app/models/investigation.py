from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Investigation(SQLModel, table=True):
    """
    One run of the Working Capital Guardian agent against a case.

    Phase 0 never produces real findings — `status` is always
    "not_implemented" and `summary` holds the stub agent's honest
    explanation of what it would do once built. The shape exists now so
    Phase 1 can start writing real findings into the same row without a
    schema migration.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    case_id: str = Field(foreign_key="case.id", index=True)
    status: str = Field(default="not_implemented")
    summary: str
    evidence_count_considered: int = 0
    started_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


class InvestigationRead(SQLModel):
    id: str
    case_id: str
    status: str
    summary: str
    evidence_count_considered: int
    started_at: datetime
    completed_at: datetime | None
