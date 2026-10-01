"""
Working Capital Guardian agent -- interface stub.

Phase 0's job is to define the entry point the rest of the application calls
and to document the contract later phases must fulfill. It does not reason
about evidence, does not call an LLM, and does not invent findings -- it
reports honestly that the investigation is not yet implemented, while still
exercising the full case -> evidence -> agent -> result pipeline end to end.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..models.evidence import Evidence


@dataclass
class InvestigationResult:
    status: str
    summary: str
    evidence_count_considered: int


class WorkingCapitalGuardian:
    """
    Future contract (Phase 1+):

        result = WorkingCapitalGuardian().investigate(case_name, evidence)

    will reconcile bank sanction/facility terms against stock, debtor,
    creditor, and ledger records; distinguish evidence-supported findings
    from unresolved ones; and return a graded breakdown of where
    working-capital capacity is being lost -- never a single confident
    verdict out of fragmented evidence.

    Phase 0 implements only the honest stub below so every layer above it
    (API routes, aiKart entrypoint, frontend) has something real to call
    and render without faking a result.
    """

    def investigate(self, case_name: str, evidence: list[Evidence]) -> InvestigationResult:
        if not evidence:
            summary = (
                "No evidence has been attached to this case yet. Once sanction "
                "terms, stock/debtor/creditor records, and ledger data are "
                "available, the Working Capital Guardian will reconcile them here."
            )
        else:
            categories = sorted({e.category for e in evidence})
            summary = (
                "Working Capital Guardian investigation is not yet implemented. "
                f"This case has {len(evidence)} evidence item(s) "
                f"({', '.join(categories)}) ready for analysis once the "
                "reconciliation and reasoning layers are built in a later phase."
            )
        return InvestigationResult(
            status="not_implemented",
            summary=summary,
            evidence_count_considered=len(evidence),
        )
