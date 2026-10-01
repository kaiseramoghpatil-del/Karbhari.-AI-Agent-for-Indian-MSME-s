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

    `status` is one of: no_evidence | complete | error (Phase 0's
    "not_implemented" is retired now that the agent does real work).
    `details_json` holds the full structured InvestigationOutcome
    (per-document extractions, aggregated facts, the deterministic
    reconciliation, and the findings list) serialized as JSON -- kept as a
    single text column rather than new tables, since Phase 1 is still
    establishing the shape of this data and a migration-free field is
    cheaper to iterate on than a normalized schema right now.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    case_id: str = Field(foreign_key="case.id", index=True)
    status: str = Field(default="no_evidence")
    summary: str
    evidence_count_considered: int = 0
    details_json: str | None = None
    started_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


class InvestigationRead(SQLModel):
    id: str
    case_id: str
    status: str
    summary: str
    evidence_count_considered: int
    details: dict | None
    started_at: datetime
    completed_at: datetime | None
