from datetime import date

from app.reconciliation.debtor_reconciliation import reconcile_debtors
from app.reconciliation.schemas import Invoice, Receipt

AS_OF = date(2026, 9, 28)


def test_tagged_receipt_pays_its_own_invoice():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=10_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 5), amount=10_000, matched_invoice_id="INV1")]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert result.invoices[0].status == "paid"
    assert result.invoices[0].balance == 0
    assert result.total_outstanding == 0


def test_partial_tagged_payment():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=10_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 5), amount=4_000, matched_invoice_id="INV1")]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert result.invoices[0].status == "partial"
    assert result.invoices[0].balance == 6_000


def test_fifo_allocation_of_untagged_receipt_across_two_invoices():
    invoices = [
        Invoice(invoice_id="INV1", date=date(2026, 8, 1), amount=5_000),
        Invoice(invoice_id="INV2", date=date(2026, 9, 1), amount=8_000),
    ]
    # One untagged receipt that should pay off the OLDER invoice first, then
    # partially pay the newer one.
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 10), amount=7_000)]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    by_id = {r.invoice_id: r for r in result.invoices}
    assert by_id["INV1"].status == "paid"
    assert by_id["INV1"].balance == 0
    assert by_id["INV2"].status == "partial"
    assert by_id["INV2"].balance == 6_000  # 7,000 - 5,000 (paid off INV1) = 2,000 applied here


def test_receipt_cannot_pay_an_invoice_dated_after_it():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 20), amount=5_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 1), amount=5_000)]  # before the invoice exists
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert result.invoices[0].status == "unpaid"
    assert len(result.unallocated_receipts) == 1


def test_unallocated_receipt_with_leftover_after_fifo():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=3_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 10), amount=5_000)]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert result.invoices[0].status == "paid"
    assert len(result.unallocated_receipts) == 1
    assert result.unallocated_receipts[0].amount == 2_000


def test_receipt_referencing_unknown_invoice_is_unallocated():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=3_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 5), amount=1_000, matched_invoice_id="INV999")]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert len(result.unallocated_receipts) == 1
    assert "unknown invoice" in result.unallocated_receipts[0].reason.lower()
    assert result.invoices[0].status == "unpaid"  # the receipt never reached INV1


def test_duplicate_invoice_id_excluded_from_totals():
    invoices = [
        Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=5_000),
        Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=5_000),  # data-entry duplicate
    ]
    result = reconcile_debtors(invoices, [], eligible_aging_days=90, as_of=AS_OF)
    assert len(result.invoices) == 1  # deduped
    assert result.total_outstanding == 5_000
    assert len(result.duplicate_invoices) == 1
    assert result.duplicate_invoices[0].occurrences == 2
    assert result.duplicate_invoices[0].excluded_amount == 5_000


def test_eligibility_cutoff_by_age():
    invoices = [
        Invoice(invoice_id="OLD", date=date(2026, 1, 1), amount=4_000),   # far over 90 days
        Invoice(invoice_id="NEW", date=date(2026, 9, 10), amount=4_000),  # within 90 days
    ]
    result = reconcile_debtors(invoices, [], eligible_aging_days=90, as_of=AS_OF)
    by_id = {r.invoice_id: r for r in result.invoices}
    assert by_id["OLD"].eligible is False
    assert by_id["NEW"].eligible is True
    assert result.total_outstanding == 8_000
    assert result.total_eligible_outstanding == 4_000


def test_untagged_receipts_do_not_bleed_across_debtors():
    """Regression test for a real bug found during demo-case construction:
    pooling multiple debtors' invoices/receipts into one call must not let
    debtor A's untagged receipt pay off debtor B's invoice just because B's
    invoice happens to be chronologically older."""
    invoices = [
        Invoice(invoice_id="A1", date=date(2026, 8, 1), amount=5_000, debtor_name="Debtor A"),
        Invoice(invoice_id="B1", date=date(2026, 7, 1), amount=5_000, debtor_name="Debtor B"),  # older
    ]
    # Debtor A pays their own invoice via an untagged receipt. If debtor
    # scoping were broken, FIFO would pay off B1 (older) instead of A1.
    receipts = [
        Receipt(receipt_id="RA", date=date(2026, 8, 10), amount=5_000, debtor_name="Debtor A"),
    ]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    by_id = {r.invoice_id: r for r in result.invoices}
    assert by_id["A1"].status == "paid"
    assert by_id["B1"].status == "unpaid"  # must NOT have been paid by A's receipt


def test_duplicate_invoice_id_across_different_debtors_is_not_a_duplicate():
    invoices = [
        Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=5_000, debtor_name="Debtor A"),
        Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=7_000, debtor_name="Debtor B"),
    ]
    result = reconcile_debtors(invoices, [], eligible_aging_days=90, as_of=AS_OF)
    assert result.duplicate_invoices == []  # same invoice_id, different debtors -- not a dupe
    assert result.total_outstanding == 12_000


def test_overpayment_is_flagged():
    invoices = [Invoice(invoice_id="INV1", date=date(2026, 9, 1), amount=1_000)]
    receipts = [Receipt(receipt_id="R1", date=date(2026, 9, 5), amount=1_500, matched_invoice_id="INV1")]
    result = reconcile_debtors(invoices, receipts, eligible_aging_days=90, as_of=AS_OF)
    assert result.invoices[0].status == "overpaid"
    assert result.invoices[0].balance == -500
