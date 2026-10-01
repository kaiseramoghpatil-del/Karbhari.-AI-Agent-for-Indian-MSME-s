from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Case(SQLModel, table=True):
    """
    A single Working Capital Guardian investigation case for one MSME
    borrower. Phase 0 only tracks identity and lifecycle status — the
    actual investigation content lives in later models/phases.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str
    business_name: str | None = None
    status: str = Field(default="open")  # open | investigating | closed (free-form for now)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class CaseCreate(SQLModel):
    name: str
    business_name: str | None = None


class CaseRead(SQLModel):
    id: str
    name: str
    business_name: str | None
    status: str
    created_at: datetime
    updated_at: datetime
