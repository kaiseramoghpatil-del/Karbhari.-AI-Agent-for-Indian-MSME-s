from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

# Suggested evidence categories for the Working Capital Guardian's eventual
# reconciliation (sanction terms vs. stock/debtor/creditor records vs.
# ledger). This is advisory metadata for Phase 0 — the frontend offers these
# as a dropdown, but "other"/uncategorized is always valid. Later phases can
# key parsing/analysis logic off this field without a schema change.
EVIDENCE_CATEGORIES: list[str] = [
    "sanction_letter",
    "stock_statement",
    "debtor_ledger",
    "creditor_ledger",
    "bank_statement",
    "other",
]


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(SQLModel, table=True):
    """
    A single piece of evidence attached to a case. Phase 0 stores the file
    and its metadata only — parsing/extraction is a future phase, tracked
    here via the `status` field so the pipeline has somewhere to report into
    without a model change later.
    """

    id: str = Field(default_factory=_uuid, primary_key=True)
    case_id: str = Field(foreign_key="case.id", index=True)
    original_filename: str
    content_type: str | None = None
    size_bytes: int
    category: str = Field(default="other")
    storage_path: str  # path relative to the configured upload directory
    status: str = Field(default="uploaded")  # uploaded | parsing | parsed | failed (future use)
    uploaded_at: datetime = Field(default_factory=_now)


class EvidenceRead(SQLModel):
    id: str
    case_id: str
    original_filename: str
    content_type: str | None
    size_bytes: int
    category: str
    status: str
    uploaded_at: datetime
