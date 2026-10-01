"""
Deterministic debtor reconciliation: invoices + receipts -> per-invoice
ageing, status, and sanction-term eligibility.

This is the module that replaces "trust the LLM's read of a ledger
subtotal" with an independently reconstructed figure. Matching tiers,
in order:

  1. Tagged match   -- a receipt that names its invoice_id is applied
                        directly to that invoice (possibly partial).
  2. FIFO allocation -- a receipt with no invoice_id (the common case for
                        Tally-style ledgers, which usually record a debtor
                        running balance, not an invoice-tagged cash book)
                        is applied against that debtor's OPEN invoices,
                        oldest first, and never against an invoice dated
                        after the receipt itself.
  3. Unallocated     -- anything left over (receipt exceeds all applicable
                        open balances, or references an unknown invoice)
                        is reported explicitly, never silently dropped.

Reconciliation is always scoped PER DEBTOR: invoices and receipts are
grouped by debtor_name before any matching happens, so an untagged
receipt can never be FIFO-allocated against a different debtor's invoice,
and a duplicate invoice_id is only flagged within the same debtor's
records. This matters even when the caller passes everything in one call
covering multiple debtors -- correctness does not depend on the caller
(agent or otherwise) remembering to call this once per debtor.

Records with no debtor_name are treated as one shared group (the normal
case for a single-debtor case, or ledgers that don't carry a name field).

Duplicate invoice_ids within the same debtor (the same invoice entered
twice -- a common ledger data-entry error) are detected and excluded from
totals, with the excluded amount reported so the effect is visible.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from .schemas import (
    DebtorReconciliationResult,
    DuplicateInvoice,
    Invoice,
    InvoiceReconciliation,
    Receipt,
    UnallocatedReceipt,
)

_UNKNOWN_DEBTOR = "__unknown__"


def _debtor_key(name: str | None) -> str:
    return name if name else _UNKNOWN_DEBTOR


def _dedupe_invoices(invoices: list[Invoice]) -> tuple[list[Invoice], list[DuplicateInvoice]]:
    seen: dict[str, Invoice] = {}
    counts: dict[str, int] = defaultdict(int)
    for inv in invoices:
        counts[inv.invoice_id] += 1
        seen.setdefault(inv.invoice_id, inv)

    duplicates = [
        DuplicateInvoice(
            invoice_id=inv_id,
            amount=seen[inv_id].amount,
            occurrences=count,
            excluded_amount=seen[inv_id].amount * (count - 1),
        )
        for inv_id, count in counts.items()
        if count > 1
    ]
    return list(seen.values()), duplicates


def _reconcile_one_debtor(
    invoices: list[Invoice],
    receipts: list[Receipt],
    eligible_aging_days: float,
    as_of: date,
) -> DebtorReconciliationResult:
    """Reconciles invoices/receipts already known to belong to ONE debtor."""
    deduped_invoices, duplicates = _dedupe_invoices(invoices)
    deduped_invoices = sorted(deduped_invoices, key=lambda i: i.date)

    balance: dict[str, float] = {inv.invoice_id: inv.amount for inv in deduped_invoices}
    paid: dict[str, float] = {inv.invoice_id: 0.0 for inv in deduped_invoices}
    invoice_by_id = {inv.invoice_id: inv for inv in deduped_invoices}

    unallocated: list[UnallocatedReceipt] = []

    tagged = [r for r in receipts if r.matched_invoice_id]
    untagged = [r for r in receipts if not r.matched_invoice_id]

    # Tier 1: tagged receipts applied directly.
    for r in tagged:
        if r.matched_invoice_id not in invoice_by_id:
            unallocated.append(
                UnallocatedReceipt(
                    receipt_id=r.receipt_id,
                    amount=r.amount,
                    reason=f"References unknown invoice_id {r.matched_invoice_id!r}.",
                )
            )
            continue
        inv_id = r.matched_invoice_id
        paid[inv_id] += r.amount
        balance[inv_id] -= r.amount

    # Tier 2: untagged receipts, FIFO oldest-open-invoice-first within this
    # debtor only, never applied to an invoice dated after the receipt.
    for r in sorted(untagged, key=lambda x: x.date):
        remaining = r.amount
        for inv in deduped_invoices:
            if remaining <= 0:
                break
            if inv.date > r.date:
                continue
            if balance[inv.invoice_id] <= 0:
                continue
            applied = min(remaining, balance[inv.invoice_id])
            balance[inv.invoice_id] -= applied
            paid[inv.invoice_id] += applied
            remaining -= applied

        if remaining > 0.01:
            unallocated.append(
                UnallocatedReceipt(
                    receipt_id=r.receipt_id,
                    amount=round(remaining, 2),
                    reason=(
                        "No invoice-tagged outstanding balance to apply this receipt "
                        "against as of its date -- possible advance payment or a "
                        "missing invoice record."
                    ),
                )
            )

    results: list[InvoiceReconciliation] = []
    total_outstanding = 0.0
    total_eligible = 0.0

    for inv in deduped_invoices:
        bal = round(balance[inv.invoice_id], 2)
        p = round(paid[inv.invoice_id], 2)
        age_days = max(0, (as_of - inv.date).days)

        if bal <= 0.01 and p > 0:
            status = "overpaid" if bal < -0.01 else "paid"
        elif p > 0:
            status = "partial"
        else:
            status = "unpaid"

        eligible = False
        reason = None
        if bal <= 0.01:
            reason = "Settled -- no outstanding balance."
        elif age_days > eligible_aging_days:
            reason = (
                f"Outstanding {age_days} days, exceeding the sanction terms' "
                f"{eligible_aging_days:.0f}-day eligibility window."
            )
        else:
            eligible = True

        if bal > 0:
            total_outstanding += bal
            if eligible:
                total_eligible += bal

        results.append(
            InvoiceReconciliation(
                invoice_id=inv.invoice_id,
                date=inv.date,
                amount=inv.amount,
                paid=p,
                balance=bal,
                status=status,
                age_days=age_days,
                eligible=eligible,
                ineligibility_reason=reason if not eligible else None,
            )
        )

    return DebtorReconciliationResult(
        invoices=results,
        total_outstanding=round(total_outstanding, 2),
        total_eligible_outstanding=round(total_eligible, 2),
        duplicate_invoices=duplicates,
        unallocated_receipts=unallocated,
        warnings=[],
    )


def reconcile_debtors(
    invoices: list[Invoice],
    receipts: list[Receipt],
    eligible_aging_days: float,
    as_of: date,
) -> DebtorReconciliationResult:
    invoices_by_debtor: dict[str, list[Invoice]] = defaultdict(list)
    for inv in invoices:
        invoices_by_debtor[_debtor_key(inv.debtor_name)].append(inv)

    # A tagged receipt belongs to whichever debtor owns the invoice it names,
    # not to the receipt's own (possibly absent or inconsistent) debtor_name
    # field -- the invoice is the authoritative link.
    invoice_owner: dict[str, str] = {
        inv.invoice_id: key for key, group in invoices_by_debtor.items() for inv in group
    }

    receipts_by_debtor: dict[str, list[Receipt]] = defaultdict(list)
    unresolved_tagged: list[Receipt] = []
    for r in receipts:
        if r.matched_invoice_id and r.matched_invoice_id in invoice_owner:
            receipts_by_debtor[invoice_owner[r.matched_invoice_id]].append(r)
        elif r.matched_invoice_id:
            unresolved_tagged.append(r)  # references an invoice_id that doesn't exist anywhere
        else:
            receipts_by_debtor[_debtor_key(r.debtor_name)].append(r)

    all_debtor_keys = set(invoices_by_debtor) | set(receipts_by_debtor)

    merged = DebtorReconciliationResult()
    for key in all_debtor_keys:
        group_result = _reconcile_one_debtor(
            invoices_by_debtor.get(key, []),
            receipts_by_debtor.get(key, []),
            eligible_aging_days,
            as_of,
        )
        merged.invoices.extend(group_result.invoices)
        merged.total_outstanding += group_result.total_outstanding
        merged.total_eligible_outstanding += group_result.total_eligible_outstanding
        merged.duplicate_invoices.extend(group_result.duplicate_invoices)
        merged.unallocated_receipts.extend(group_result.unallocated_receipts)

    for r in unresolved_tagged:
        merged.unallocated_receipts.append(
            UnallocatedReceipt(
                receipt_id=r.receipt_id,
                amount=r.amount,
                reason=f"References unknown invoice_id {r.matched_invoice_id!r}.",
            )
        )

    merged.total_outstanding = round(merged.total_outstanding, 2)
    merged.total_eligible_outstanding = round(merged.total_eligible_outstanding, 2)
    merged.invoices.sort(key=lambda i: i.date)

    if merged.duplicate_invoices:
        merged.warnings.append(
            f"{len(merged.duplicate_invoices)} duplicate invoice_id(s) found (within the same "
            f"debtor) and excluded from totals after the first occurrence -- see duplicate_invoices."
        )
    if len(all_debtor_keys) > 1:
        merged.warnings.append(
            f"Reconciled {len(all_debtor_keys)} debtors separately; receipts were never "
            f"allocated across different debtors' invoices."
        )

    return merged
