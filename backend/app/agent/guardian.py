"""
Working Capital Guardian -- public entry point.

Thin wrapper around investigator.run_investigation(): builds the ONE
deterministic headline finding directly from calculate_drawing_power's
output (never from the agent's own words), combines it with whatever
additional findings the agent produced, and packages the full tool trace
for traceability. The agent never computes or restates the headline gap
number -- it's constructed here, in code, from the toolbox's own last
result.

This module's public interface (WorkingCapitalGuardian.investigate) is
unchanged from Phase 0/1 on purpose -- routers and tests depend on it.
What changed is everything behind it: Phase 1's fixed two-call pipeline
is now a real bounded investigation (see investigator.py).
"""

from __future__ import annotations

from collections import Counter

from ..llm import get_llm_client
from ..llm.base import LLMError
from ..models.evidence import Evidence
from .investigator import run_investigation
from .schemas import Finding, InvestigationOutcome


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


class WorkingCapitalGuardian:
    def investigate(self, case_name: str, evidence: list[Evidence]) -> InvestigationResult:
        if not evidence:
            return InvestigationResult(
                status="no_evidence",
                summary=(
                    "No evidence has been attached to this case yet. Once sanction terms, "
                    "stock/debtor/creditor records, and ledger data are available, the "
                    "Working Capital Guardian will investigate them here."
                ),
                evidence_count_considered=0,
            )

        try:
            llm = get_llm_client()
        except LLMError as exc:
            return InvestigationResult(
                status="error",
                summary=f"Investigation could not start: {exc}",
                evidence_count_considered=len(evidence),
            )

        run = run_investigation(llm, evidence)

        headline = _headline_finding(run.toolbox.last_dp_result)
        findings: list[Finding] = ([headline] if headline else []) + run.findings

        coverage_gap = _consistency_coverage_gap(evidence, run.toolbox.last_consistency)
        if coverage_gap:
            findings.append(coverage_gap)

        outcome = InvestigationOutcome(
            tool_trace=run.trace,
            debtor_reconciliation=run.toolbox.last_debtor_reconciliation,
            consistency=run.toolbox.last_consistency,
            reconciliation=run.toolbox.last_dp_result,
            findings=findings,
            stopped_reason=run.stopped_reason,
        )

        if run.stopped_reason == "agent_finished":
            status = "complete"
        elif run.stopped_reason.startswith("llm_error"):
            status = "error"
        else:
            status = "incomplete"

        summary = _build_summary(run.toolbox.last_dp_result, findings, run.stopped_reason, len(run.trace))

        return InvestigationResult(
            status=status,
            summary=summary,
            evidence_count_considered=len(evidence),
            outcome=outcome,
        )


def _headline_finding(reconciliation) -> Finding | None:
    if reconciliation is None:
        return Finding(
            title="Drawing Power was not calculated",
            status="unresolved",
            explanation=(
                "The investigation did not reach a Drawing Power calculation. See the "
                "tool trace for what evidence was reviewed."
            ),
        )

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
                f"Based on the available stock/debtor/creditor figures and sanction terms, "
                f"the calculated Drawing Power is {reconciliation.calculated_dp}. No "
                f"bank-reported Drawing Power or current outstanding figure was found to "
                f"compare it against. Missing: " + "; ".join(reconciliation.missing_inputs) + "."
            ),
        )

    if gap > 0:
        status = "supported" if not reconciliation.assumptions_used else "unresolved"
        title = "Calculated Drawing Power appears to exceed what the bank is currently recognising"
        explanation = (
            f"Based on the sanction terms and the independently reconciled stock/debtor/"
            f"creditor records, the calculated Drawing Power is {reconciliation.calculated_dp}, "
            f"against a {comparison_label} of {reconciliation.comparison_value}. That is a gap "
            f"of {gap} that appears supportable under the supplied facility terms, within the "
            f"existing sanctioned limit -- not a request for more credit. This is not a "
            f"guarantee the bank will recompute or release this amount."
        )
        amount_impact = gap
    elif gap < 0:
        status = "ineligible_contradicted"
        title = "No evidence of unused capacity -- recorded usage exceeds the calculated figure"
        explanation = (
            f"The calculated Drawing Power from the available records is "
            f"{reconciliation.calculated_dp}, which is LOWER than the {comparison_label} of "
            f"{reconciliation.comparison_value} by {abs(gap)}. This evidence does not support "
            f"a claim of lost working-capital capacity."
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

    return Finding(title=title, status=status, explanation=explanation, amount_impact=amount_impact)


def _consistency_coverage_gap(evidence: list[Evidence], consistency) -> Finding | None:
    """
    The agent repeatedly (across multiple live runs, several prompt
    rewrites, and a model upgrade) chose not to call check_consistency even
    when the evidence clearly supported it -- a real, observed limitation,
    not a hypothetical. Rather than keep tuning the prompt indefinitely,
    this is the code-level backstop the project's own principle calls for:
    don't rely on the agent's discipline for something that matters.

    This never fabricates a variance finding (it has no numbers to do that
    with) -- it only flags, honestly, that a check which looks applicable
    was not run in this particular investigation, based on a cheap,
    deterministic signal (more than one evidence item sharing a category
    that's normally period-specific), not on re-reading documents.
    """
    if consistency is not None:
        return None  # the agent actually ran it -- nothing to flag

    period_sensitive = {"stock_statement", "debtor_ledger", "creditor_ledger", "bank_statement"}
    counts = Counter(e.category for e in evidence)
    repeated_categories = [c for c, n in counts.items() if n > 1 and c in period_sensitive]
    if not repeated_categories:
        return None

    return Finding(
        title="Period-over-period consistency was not checked in this run",
        status="unresolved",
        explanation=(
            f"This case has more than one evidence item categorized as "
            f"{', '.join(repeated_categories)}, which often means figures for different "
            f"periods are present, but this investigation run did not execute a "
            f"consistency check across them. If these documents cover different dates, "
            f"verify whether the figures move consistently before relying on the most "
            f"recent one alone -- a large unexplained swing between periods can itself be "
            f"worth investigating."
        ),
    )


def _build_summary(reconciliation, findings: list[Finding], stopped_reason: str, step_count: int) -> str:
    supported = sum(1 for f in findings if f.status == "supported")
    unresolved = sum(1 for f in findings if f.status == "unresolved")
    contradicted = sum(1 for f in findings if f.status == "ineligible_contradicted")

    if stopped_reason != "agent_finished":
        prefix = (
            f"Investigation stopped early ({stopped_reason.replace('_', ' ')}) after "
            f"{step_count} step(s). "
        )
    else:
        prefix = f"Investigation completed in {step_count} step(s). "

    if reconciliation and reconciliation.can_calculate and reconciliation.gap is not None and reconciliation.gap > 0:
        headline = f"Calculated Drawing Power exceeds the reported figure by {reconciliation.gap}."
    elif reconciliation and reconciliation.can_calculate and reconciliation.gap is not None:
        headline = "No evidence of unused capacity was found."
    elif reconciliation and reconciliation.can_calculate:
        headline = f"Drawing Power calculated at {reconciliation.calculated_dp}; nothing to compare it against."
    else:
        headline = "Drawing Power could not be fully calculated from the evidence provided."

    return (
        f"{prefix}{headline} {len(findings)} finding(s) "
        f"({supported} supported, {unresolved} unresolved, {contradicted} contradicted/ineligible)."
    )
