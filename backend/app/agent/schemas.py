"""
Structured shapes for the Working Capital Guardian investigation.

These are plain pydantic models (not SQLModel tables). The whole bundle
gets serialized into Investigation.details_json for traceability; nothing
here is persisted as its own table yet.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from ..calculations.drawing_power import ReconciliationResult
from ..reconciliation.schemas import ConsistencyResult, DebtorReconciliationResult

FindingStatus = Literal["supported", "unresolved", "ineligible_contradicted"]


class Finding(BaseModel):
    title: str
    status: FindingStatus
    explanation: str
    amount_impact: float | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    """One step of the bounded investigation loop -- what the agent chose to
    do, why, and what the tool actually returned. This is the trace that
    makes the investigation demonstrable and debuggable rather than a black
    box, and it's real: generated from the actual tool calls made during
    this run, not reconstructed after the fact."""

    step: int
    thought: str
    tool: str
    tool_input: dict[str, Any] = Field(default_factory=dict)
    tool_output: dict[str, Any] = Field(default_factory=dict)
    output_summary: str


class InvestigationOutcome(BaseModel):
    """The full structured result of one investigation run."""

    tool_trace: list[ToolCallRecord] = Field(default_factory=list)
    debtor_reconciliation: DebtorReconciliationResult | None = None
    consistency: ConsistencyResult | None = None
    reconciliation: ReconciliationResult | None = None
    findings: list[Finding] = Field(default_factory=list)
    stopped_reason: str = ""
