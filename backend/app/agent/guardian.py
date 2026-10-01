"""
Working Capital Guardian -- Phase 1 real pipeline.

    extract (LLM, per-case)
      -> aggregate (deterministic)
      -> reconcile Drawing Power (deterministic -- see calculations/drawing_power.py)
      -> headline finding (deterministic, built from the reconciliation result)
      -> synthesize additional findings (LLM, given the deterministic result as ground truth)

"The LLM reasons, code calculates": the only numbers that drive the
headline finding come from calculations/drawing_power.py. The LLM extracts
facts from messy documents and reasons about contradictions/ambiguities,
but never computes or restates the capacity-gap figure itself.
"""

from __future__ import annotations

import json
import logging

from ..calculations.drawing_power import reconcile_drawing_power
from ..config import UPLOAD_DIR
from ..llm import get_llm_client
from ..llm.base import LLMError
from ..models.evidence import Evidence
from ..services.document_extraction import extract_text
from .prompts import EXTRACTION_SYSTEM_PROMPT, FINDINGS_SYSTEM_PROMPT
from .schemas import (
    AggregatedFacts,
    EvidenceExtraction,
    ExtractedFacts,
    FieldConflict,
    Finding,
    InvestigationOutcome,
    ReconciliationResult,
)

logger = logging.getLogger(__name__)


class InvestigationResult:
    def __init__(
        self,
        status: str,
        summary: str,
        evidence_count_considered: int,
        outcome: InvestigationOutcome | None = None,
    ):
        self.status = status
        self.summary = summary
        self.evidence_count_considered = evidence_count_considered
        self.outcome = outcome


# Which document type each aggregated field should preferentially come from
# when more than one document mentions it.
FIELD_SOURCE_PREFERENCE: dict[str, list[str]] = {
    "sanctioned_limit": ["sanction_letter"],
    "stock_margin_pct": ["sanction_letter"],
    "debtor_margin_pct": ["sanction_letter"],
    "debtor_eligible_aging_days": ["sanction_letter"],
    "stock_value": ["stock_statement"],
    "total_debtor_value": ["debtor_ledger"],
    "eligible_debtor_value": ["debtor_ledger"],
    "creditor_value": ["creditor_ledger"],
    "reported_drawing_power": ["bank_statement"],
    "current_outstanding_or_utilization": ["bank_statement"],
}


class WorkingCapitalGuardian:
    def __init__(self):
        self._llm = None  # lazy: don't require an API key just to import this module

    def _llm_client(self):
        if self._llm is None:
            self._llm = get_llm_client()
        return self._llm

    def investigate(self, case_name: str, evidence: list[Evidence]) -> InvestigationResult:
        if not evidence:
            return InvestigationResult(
                status="no_evidence",
                summary=(
                    "No evidence has been attached to this case yet. Once sanction terms, "
                    "stock/debtor/creditor records, and ledger data are available, the "
                    "Working Capital Guardian will reconcile them here."
                ),
                evidence_count_considered=0,
            )

        try:
            extractions = self._extract_all(evidence)
        except LLMError as exc:
            return InvestigationResult(
                status="error",
                summary=f"Investigation could not run: {exc}",
                evidence_count_considered=len(evidence),
            )

        aggregated = self._aggregate(extractions)
        reconciliation = reconcile_drawing_power(aggregated)
        headline_finding = self._headline_finding(reconciliation)

        try:
            extra_findings = self._synthesize_findings(extractions, aggregated, reconciliation)
        except LLMError as exc:
            extra_findings = []
            logger.warning("Findings synthesis failed: %s", exc)

        findings = [headline_finding] + extra_findings

        outcome = InvestigationOutcome(
            extractions=extractions,
            aggregated_facts=aggregated,
            reconciliation=reconciliation,
            findings=findings,
        )

        return InvestigationResult(
            status="complete",
            summary=self._build_summary(reconciliation, findings),
            evidence_count_considered=len(evidence),
            outcome=outcome,
        )

    # ---- Stage 1: document understanding (LLM) ----

    def _extract_all(self, evidence: list[Evidence]) -> list[EvidenceExtraction]:
        doc_blocks = []
        for e in evidence:
            file_path = UPLOAD_DIR / e.storage_path
            text = extract_text(file_path, e.content_type, e.original_filename)
            doc_blocks.append(
                f"=== Evidence {e.id} ===\n"
                f"Filename: {e.original_filename}\n"
                f"Uploader category: {e.category}\n"
                f"--- Extracted text ---\n{text}\n"
            )
        user_prompt = "\n\n".join(doc_blocks)

        raw = self._llm_client().generate_json(
            EXTRACTION_SYSTEM_PROMPT, user_prompt, temperature=0.1
        )
        parsed = _parse_json_object(raw)

        extractions: list[EvidenceExtraction] = []
        for e in evidence:
            doc_data = parsed.get(e.id, {}) if isinstance(parsed, dict) else {}
            try:
                facts = ExtractedFacts.model_validate(doc_data)
            except Exception:  # noqa: BLE001
                facts = ExtractedFacts(
                    notes="Could not parse the extraction output for this document."
                )
            extractions.append(
                EvidenceExtraction(
                    evidence_id=e.id,
                    original_filename=e.original_filename,
                    category=e.category,
                    facts=facts,
                )
            )
        return extractions

    # ---- Aggregation across documents (deterministic) ----

    def _aggregate(self, extractions: list[EvidenceExtraction]) -> AggregatedFacts:
        agg = AggregatedFacts()
        by_id = {ex.evidence_id: ex for ex in extractions}

        for field, preferred_types in FIELD_SOURCE_PREFERENCE.items():
            candidates = [
                (ex.evidence_id, getattr(ex.facts, field))
                for ex in extractions
                if getattr(ex.facts, field) is not None
            ]
            if not candidates:
                agg.missing_fields.append(field)
                continue

            preferred = [
                (eid, val)
                for eid, val in candidates
                if by_id[eid].facts.document_type_guess in preferred_types
            ]
            chosen_value = (preferred or candidates)[0][1]
            setattr(agg, field, chosen_value)

            distinct_values = {val for _, val in candidates}
            if len(distinct_values) > 1:
                agg.conflicts.append(
                    FieldConflict(
                        field=field,
                        values=[{"evidence_id": eid, "value": val} for eid, val in candidates],
                    )
                )
        return agg

    # ---- Headline finding (deterministic, built from the reconciliation result) ----

    def _headline_finding(self, reconciliation: ReconciliationResult) -> Finding:
        if not reconciliation.can_calculate:
            return Finding(
                title="Drawing Power could not be independently calculated",
                status="unresolved",
                explanation=(
                    "The evidence provided does not include everything needed to calculate "
                    "Drawing Power from the sanction terms. Missing: "
                    + "; ".join(reconciliation.missing_inputs)
                    + "."
                ),
            )

        gap = reconciliation.gap
        comparison_label = reconciliation.comparison_basis.replace("_", " ")

        if gap is None:
            return Finding(
                title="Drawing Power calculated, but nothing to compare it against",
                status="unresolved",
                explanation=(
                    f"Based on the available stock/debtor/creditor figures and sanction "
                    f"terms, the calculated Drawing Power is {reconciliation.calculated_dp}. "
                    "No bank-reported Drawing Power or current outstanding figure was found "
                    "to compare it against. Missing: "
                    + "; ".join(reconciliation.missing_inputs)
                    + "."
                ),
            )

        if gap > 0:
            status = "supported" if not reconciliation.assumptions_used else "unresolved"
            title = "Calculated Drawing Power exceeds what the bank is currently recognising"
            explanation = (
                f"Based on the sanction terms and the business's own stock/debtor/creditor "
                f"records, the calculated Drawing Power is {reconciliation.calculated_dp}, "
                f"against a {comparison_label} of {reconciliation.comparison_value}. That is "
                f"a gap of {gap} within the existing sanctioned limit -- not a request for "
                f"more credit, but capacity inside the facility the business already has."
            )
            amount_impact = gap
        elif gap < 0:
            status = "ineligible_contradicted"
            title = "No evidence of unused capacity -- recorded usage exceeds the calculated figure"
            explanation = (
                f"The calculated Drawing Power from the available records is "
                f"{reconciliation.calculated_dp}, which is LOWER than the {comparison_label} "
                f"of {reconciliation.comparison_value} by {abs(gap)}. This evidence does not "
                f"support a claim of lost working-capital capacity -- if anything it points "
                f"the other way and is worth the business's attention."
            )
            amount_impact = None
        else:
            status = "ineligible_contradicted"
            title = "No material gap found"
            explanation = (
                f"The calculated Drawing Power ({reconciliation.calculated_dp}) matches the "
                f"{comparison_label} ({reconciliation.comparison_value}) within an immaterial "
                f"margin. The evidence does not support a finding of lost capacity."
            )
            amount_impact = None

        if reconciliation.assumptions_used:
            explanation += " Note: " + " ".join(reconciliation.assumptions_used)

        return Finding(
            title=title,
            status=status,
            explanation=explanation,
            amount_impact=amount_impact,
        )

    # ---- Stage 2: findings synthesis (LLM) ----

    def _synthesize_findings(
        self,
        extractions: list[EvidenceExtraction],
        aggregated: AggregatedFacts,
        reconciliation: ReconciliationResult,
    ) -> list[Finding]:
        payload = {
            "per_document_extractions": [ex.model_dump() for ex in extractions],
            "aggregated_facts": aggregated.model_dump(),
            "deterministic_reconciliation": reconciliation.model_dump(),
        }
        user_prompt = json.dumps(payload, indent=2, default=str)

        raw = self._llm_client().generate_json(
            FINDINGS_SYSTEM_PROMPT, user_prompt, temperature=0.3
        )
        parsed = _parse_json_object(raw)
        findings_data = parsed.get("findings", []) if isinstance(parsed, dict) else []

        findings = []
        for item in findings_data:
            try:
                findings.append(Finding.model_validate(item))
            except Exception:  # noqa: BLE001
                continue
        return findings

    # ---- Summary line ----

    def _build_summary(self, reconciliation: ReconciliationResult, findings: list[Finding]) -> str:
        supported = sum(1 for f in findings if f.status == "supported")
        unresolved = sum(1 for f in findings if f.status == "unresolved")
        contradicted = sum(1 for f in findings if f.status == "ineligible_contradicted")

        if reconciliation.can_calculate and reconciliation.gap is not None and reconciliation.gap > 0:
            headline = f"Calculated Drawing Power exceeds the reported figure by {reconciliation.gap}."
        elif reconciliation.can_calculate and reconciliation.gap is not None:
            headline = "No evidence of unused capacity was found."
        elif reconciliation.can_calculate:
            headline = f"Drawing Power calculated at {reconciliation.calculated_dp}; nothing to compare it against."
        else:
            headline = "Drawing Power could not be fully calculated from the evidence provided."

        return (
            f"{headline} {len(findings)} finding(s) produced "
            f"({supported} supported, {unresolved} unresolved, {contradicted} contradicted/ineligible)."
        )


def _parse_json_object(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        # strict=False: Gemini sometimes embeds literal newline/tab characters
        # inside quoted string values (e.g. a multi-line quote) instead of
        # escaping them as \n/\t. That's invalid strict JSON but unambiguous
        # to parse permissively, and rejecting it would silently discard an
        # otherwise-correct extraction.
        return json.loads(text, strict=False)
    except json.JSONDecodeError as exc:
        logger.warning(
            "Failed to parse LLM JSON output (%s). First 500 chars: %r", exc, text[:500]
        )
        return {}
