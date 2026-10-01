"""
The investigator's tool belt.

Each tool is either:
  - a thin, fully deterministic wrapper around evidence storage/text
    extraction (list_evidence, read_evidence), or
  - a thin, fully deterministic wrapper around app/reconciliation and
    app/calculations (reconcile_debtors, check_consistency,
    calculate_drawing_power).

The agent decides WHEN to call these and WHAT to pass in (it reads messy
evidence text and structures it into tool arguments); the tools themselves
never call an LLM and never guess. calculate_drawing_power additionally
enforces the project's core rule in code, not just in the prompt: if a
debtor reconciliation has already been run in this session, its
independently-reconstructed eligible-debtor figure silently overrides
whatever the agent passed for eligible_debtor_value, and the override is
recorded so it's visible, not hidden.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from ..calculations.drawing_power import DrawingPowerInputs, ReconciliationResult, reconcile_drawing_power
from ..config import UPLOAD_DIR
from ..models.evidence import Evidence
from ..reconciliation.consistency import check_consistency as _check_consistency
from ..reconciliation.debtor_reconciliation import reconcile_debtors as _reconcile_debtors
from ..reconciliation.schemas import (
    ConsistencyResult,
    DebtorReconciliationResult,
    Invoice,
    PeriodFigure,
    Receipt,
)
from ..services.document_extraction import extract_text

TOOL_CATALOG = """
TOOLS AVAILABLE

1. list_evidence
   Input: {}
   Output: the case's evidence items -- evidence_id, filename, category.
   Always call this first.

2. read_evidence
   Input: {"evidence_id": "<id from list_evidence>"}
   Output: the raw extracted text of that document. This is YOUR job to
   read and interpret -- pull out whatever facts and line items you need.
   No other tool reads documents for you.

3. reconcile_debtors
   Input: {
     "invoices": [{"invoice_id": str, "date": "YYYY-MM-DD", "amount": number,
                    "debtor_name": str or null}, ...],
     "receipts": [{"receipt_id": str, "date": "YYYY-MM-DD", "amount": number,
                    "matched_invoice_id": str or null, "debtor_name": str or null}, ...],
     "eligible_aging_days": number,   // from the sanction terms
     "as_of": "YYYY-MM-DD"            // the evidence's own reference date, NOT today
   }
   Output: per-invoice status/ageing/eligibility, total outstanding, total
   ELIGIBLE outstanding, duplicate invoices found, unallocated receipts.
   A receipt with no matched_invoice_id is allocated FIFO against that SAME
   debtor's oldest open invoices -- never against a different debtor's
   invoice, regardless of dates. You may pass every debtor's invoices and
   receipts in ONE call (include debtor_name on each so they can be told
   apart) -- the tool itself keeps debtors separate internally; you do not
   need to call this once per debtor. Call this whenever you have invoice-
   and/or receipt-level debtor data, not just a single pre-totalled
   subtotal line.

4. check_consistency
   Input: {
     "field_history": {
       "<field_name>": [{"period_label": str, "value": number}, ...]  // chronological order
     },
     "threshold_pct": number (optional, default 20)
   }
   Output: flags for any field that swung more than threshold_pct between
   consecutive periods. Use this whenever evidence covers more than one
   period for the same figure (e.g. two stock statements, or a debtor
   ledger from two different dates).

5. calculate_drawing_power
   Input: {
     "sanctioned_limit": number or null,
     "stock_margin_pct": number or null,
     "debtor_margin_pct": number or null,
     "stock_value": number or null,
     "eligible_debtor_value": number or null,   // ignored/overridden if you already called reconcile_debtors
     "creditor_value": number or null,
     "reported_drawing_power": number or null,
     "current_outstanding_or_utilization": number or null
   }
   Output: the calculated Drawing Power, what it's compared against, and
   the gap. This is the ONLY source of that number -- never state a
   capacity-gap figure yourself that didn't come from this tool's output.

finish_investigation is NOT one of the tools above and is never called via
"action": "call_tool" -- it is the OTHER possible action, described in
RESPONSE FORMAT below. Do not put "finish_investigation" in the "tool"
field; set "action" to "finish" directly.
""".strip()


class InvestigatorToolbox:
    def __init__(self, evidence: list[Evidence]):
        self._evidence_by_id = {e.id: e for e in evidence}
        self._text_cache: dict[str, str] = {}
        self.last_debtor_reconciliation: DebtorReconciliationResult | None = None
        self.last_consistency: ConsistencyResult | None = None
        self.last_dp_result: ReconciliationResult | None = None

    def evidence_list_payload(self) -> list[dict]:
        return [
            {"evidence_id": e.id, "filename": e.original_filename, "category": e.category}
            for e in self._evidence_by_id.values()
        ]

    def _read_text(self, evidence_id: str) -> str:
        if evidence_id not in self._text_cache:
            e = self._evidence_by_id[evidence_id]
            file_path = UPLOAD_DIR / e.storage_path
            self._text_cache[evidence_id] = extract_text(file_path, e.content_type, e.original_filename)
        return self._text_cache[evidence_id]

    def execute(self, tool: str, tool_input: dict[str, Any]) -> tuple[dict, str]:
        """Returns (raw_output_dict, human_summary_for_trace)."""
        if tool == "list_evidence":
            items = self.evidence_list_payload()
            return {"evidence": items}, f"{len(items)} evidence item(s) listed."

        if tool == "read_evidence":
            evidence_id = tool_input.get("evidence_id")
            if evidence_id not in self._evidence_by_id:
                return {"error": f"Unknown evidence_id {evidence_id!r}"}, "Unknown evidence_id."
            text = self._read_text(evidence_id)
            e = self._evidence_by_id[evidence_id]
            return (
                {"evidence_id": evidence_id, "filename": e.original_filename, "text": text},
                f"Read {e.original_filename} ({len(text)} chars).",
            )

        if tool == "reconcile_debtors":
            return self._reconcile_debtors(tool_input)

        if tool == "check_consistency":
            field_history = {
                field: [PeriodFigure(**p) for p in periods]
                for field, periods in (tool_input.get("field_history") or {}).items()
            }
            threshold = tool_input.get("threshold_pct", 20.0)
            result = _check_consistency(field_history, threshold_pct=threshold)
            self.last_consistency = result
            summary = (
                f"{len(result.flags)} variance flag(s) found."
                if result.flags
                else "No material period-over-period variance found."
            )
            return result.model_dump(mode="json"), summary

        if tool == "calculate_drawing_power":
            return self._calculate_drawing_power(tool_input)

        return {"error": f"Unknown tool {tool!r}"}, "Unknown tool."

    def _reconcile_debtors(self, tool_input: dict[str, Any]) -> tuple[dict, str]:
        try:
            invoices = [Invoice(**i) for i in tool_input.get("invoices", [])]
            receipts = [Receipt(**r) for r in tool_input.get("receipts", [])]
            eligible_aging_days = float(tool_input["eligible_aging_days"])
            as_of = date.fromisoformat(tool_input["as_of"])
        except (KeyError, ValueError, TypeError) as exc:
            return {"error": f"Invalid input: {exc}"}, f"Invalid input to reconcile_debtors: {exc}"

        result = _reconcile_debtors(invoices, receipts, eligible_aging_days, as_of)
        self.last_debtor_reconciliation = result
        summary = (
            f"Reconciled {len(invoices)} invoice(s) / {len(receipts)} receipt(s): "
            f"total outstanding {result.total_outstanding}, eligible outstanding "
            f"{result.total_eligible_outstanding}"
        )
        if result.duplicate_invoices:
            summary += f", {len(result.duplicate_invoices)} duplicate invoice(s) excluded"
        if result.unallocated_receipts:
            summary += f", {len(result.unallocated_receipts)} unallocated receipt(s)"
        return result.model_dump(mode="json"), summary

    def _calculate_drawing_power(self, tool_input: dict[str, Any]) -> tuple[dict, str]:
        inputs = DrawingPowerInputs(
            sanctioned_limit=tool_input.get("sanctioned_limit"),
            stock_margin_pct=tool_input.get("stock_margin_pct"),
            debtor_margin_pct=tool_input.get("debtor_margin_pct"),
            stock_value=tool_input.get("stock_value"),
            eligible_debtor_value=tool_input.get("eligible_debtor_value"),
            creditor_value=tool_input.get("creditor_value"),
            reported_drawing_power=tool_input.get("reported_drawing_power"),
            current_outstanding_or_utilization=tool_input.get("current_outstanding_or_utilization"),
        )

        override_note = None
        if self.last_debtor_reconciliation is not None:
            reconciled_value = self.last_debtor_reconciliation.total_eligible_outstanding
            agent_value = inputs.eligible_debtor_value
            if agent_value is not None and abs(agent_value - reconciled_value) > 1:
                override_note = (
                    f"eligible_debtor_value was overridden: the agent supplied {agent_value}, "
                    f"but the independently reconciled figure from reconcile_debtors "
                    f"({reconciled_value}) was used instead -- that reconciliation is the "
                    f"authoritative source, not a document subtotal or agent estimate."
                )
            inputs.eligible_debtor_value = reconciled_value

        result = reconcile_drawing_power(inputs)
        if override_note:
            result.assumptions_used = [override_note, *result.assumptions_used]

        self.last_dp_result = result

        if not result.can_calculate:
            summary = f"Could not calculate -- missing: {'; '.join(result.missing_inputs)}"
        else:
            summary = (
                f"Calculated DP {result.calculated_dp}, compared against "
                f"{result.comparison_basis} ({result.comparison_value}): gap {result.gap}"
            )
        return result.model_dump(mode="json"), summary
