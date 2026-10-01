"""
Structured shapes for the Working Capital Guardian pipeline.

These are plain pydantic models (not SQLModel tables) -- they describe the
LLM's input/output contracts and the deterministic calculator's output.
The whole bundle gets serialized into Investigation.details_json for
traceability; nothing here is persisted as its own table in Phase 1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FindingStatus = Literal["supported", "unresolved", "ineligible_contradicted"]


class EvidenceSnippet(BaseModel):
    field: str
    quote: str


class ExtractedFacts(BaseModel):
    """What the LLM pulled out of ONE evidence document."""

    document_type_guess: str = "unclear"
    sanctioned_limit: float | None = None
    stock_margin_pct: float | None = None
    debtor_margin_pct: float | None = None
    debtor_eligible_aging_days: float | None = None
    stock_value: float | None = None
    total_debtor_value: float | None = None
    eligible_debtor_value: float | None = None
    creditor_value: float | None = None
    statement_date: str | None = None
    reported_drawing_power: float | None = None
    current_outstanding_or_utilization: float | None = None
    evidence_snippets: list[EvidenceSnippet] = Field(default_factory=list)
    notes: str = ""


class EvidenceExtraction(BaseModel):
    """ExtractedFacts tied back to the evidence row it came from."""

    evidence_id: str
    original_filename: str
    category: str
    facts: ExtractedFacts


class FieldConflict(BaseModel):
    field: str
    values: list[dict] = Field(default_factory=list)  # [{"evidence_id": ..., "value": ...}]


class AggregatedFacts(BaseModel):
    """
    Deterministic aggregation of ExtractedFacts across all evidence for a
    case -- one value per field, chosen by a fixed preference order per
    field (see guardian.py), with disagreements recorded rather than
    silently dropped.
    """

    sanctioned_limit: float | None = None
    stock_margin_pct: float | None = None
    debtor_margin_pct: float | None = None
    debtor_eligible_aging_days: float | None = None
    stock_value: float | None = None
    total_debtor_value: float | None = None
    eligible_debtor_value: float | None = None
    creditor_value: float | None = None
    reported_drawing_power: float | None = None
    current_outstanding_or_utilization: float | None = None
    conflicts: list[FieldConflict] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class ReconciliationResult(BaseModel):
    """
    Deterministic Drawing Power calculation -- see
    app/calculations/drawing_power.py. No LLM involvement in these numbers.
    """

    calculated_dp: float | None = None
    comparison_basis: Literal["reported_drawing_power", "current_outstanding", "none"] = "none"
    comparison_value: float | None = None
    gap: float | None = None
    assumptions_used: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    can_calculate: bool = False


class Finding(BaseModel):
    title: str
    status: FindingStatus
    explanation: str
    amount_impact: float | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)


class InvestigationOutcome(BaseModel):
    """The full structured result of one investigation run."""

    extractions: list[EvidenceExtraction] = Field(default_factory=list)
    aggregated_facts: AggregatedFacts | None = None
    reconciliation: ReconciliationResult | None = None
    findings: list[Finding] = Field(default_factory=list)
