"""
Bundled demo case for aiKart's "Try Me Now" sandbox.

aiKart's manifest inputs are text-only (no file upload) and the sandbox has no
LLM API key, so the live agent can't read documents there. This module lets a
buyer still see a real investigation: the six documents in
`ASSETS FOR TESTING/` (Suryoday Textiles) are transcribed below into the same
structured line items the agent would pass to its tools, and then run through
the REAL deterministic engines -- reconcile_debtors, check_consistency and
reconcile_drawing_power -- plus the same headline-finding builder the web app
uses. Every number in the output is computed here at run time, not stored.

The transcription replaces only the agent's document-reading step, and the
output says so. Running the same documents through the live agent in the web
app produced the same figures (calculated DP Rs 25,70,000 vs Rs 23,50,000
recognised, gap Rs 2,20,000).
"""

from __future__ import annotations

from datetime import date

from ..agent.guardian import _headline_finding
from ..calculations.drawing_power import DrawingPowerInputs, reconcile_drawing_power
from ..reconciliation.consistency import check_consistency
from ..reconciliation.debtor_reconciliation import reconcile_debtors
from ..reconciliation.schemas import Invoice, PeriodFigure, Receipt

BUSINESS = "Suryoday Textiles Pvt Ltd"
AS_OF = date(2026, 9, 30)  # month-end of the latest (September) stock statement

# sanction_letter.pdf
SANCTION = {"limit": 5_000_000, "stock_margin_pct": 25.0, "debtor_margin_pct": 40.0, "eligible_days": 90}

# stock_statement_june2026.txt / stock_statement_sep2026.pdf
PERIODS = {
    "stock_value": [("June 2026", 2_400_000), ("September 2026", 3_000_000)],
    "sundry_debtors": [("June 2026", 1_700_000), ("September 2026", 2_200_000)],
    "sundry_creditors": [("June 2026", 300_000), ("September 2026", 400_000)],
}
REPORTED_DP = 2_350_000  # "Drawing Power recognised by branch", September statement

# debtor_invoice_ledger.xlsx
INVOICES = [
    Invoice(invoice_id="INV-1001", debtor_name="Rangoli Garments", date=date(2026, 8, 10), amount=500_000),
    Invoice(invoice_id="INV-1002", debtor_name="Rangoli Garments", date=date(2026, 5, 1), amount=300_000),
    Invoice(invoice_id="INV-1003", debtor_name="Om Textile Traders", date=date(2026, 7, 20), amount=700_000),
    Invoice(invoice_id="INV-1004", debtor_name="Om Textile Traders", date=date(2026, 9, 5), amount=400_000),
    Invoice(invoice_id="INV-1005", debtor_name="Shree Fabrics Co", date=date(2026, 6, 15), amount=600_000),
    Invoice(invoice_id="INV-1006", debtor_name="Shree Fabrics Co", date=date(2026, 9, 15), amount=300_000),
]
# debtor_receipts.csv
RECEIPTS = [
    Receipt(receipt_id="RCPT-501", debtor_name="Rangoli Garments", date=date(2026, 9, 1), amount=200_000, matched_invoice_id="INV-1002"),
    Receipt(receipt_id="RCPT-502", debtor_name="Om Textile Traders", date=date(2026, 9, 10), amount=700_000, matched_invoice_id="INV-1003"),
    Receipt(receipt_id="RCPT-503", debtor_name="Shree Fabrics Co", date=date(2026, 9, 20), amount=100_000, matched_invoice_id="INV-1005"),
]
# creditor_ledger.csv
CREDITORS = [("Nakoda Yarns Pvt Ltd", 250_000), ("Vishal Dyeing Works", 150_000)]

EVIDENCE = [
    "sanction_letter.pdf", "stock_statement_june2026.txt", "stock_statement_sep2026.pdf",
    "debtor_invoice_ledger.xlsx", "debtor_receipts.csv", "creditor_ledger.csv",
]

_STATUS_LABEL = {"supported": "SUPPORTED", "unresolved": "UNRESOLVED", "ineligible_contradicted": "CONTRADICTED"}


def inr(v: float) -> str:
    """Indian digit grouping: 2570000 -> 'Rs 25,70,000'."""
    s = str(int(round(abs(v))))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if v < 0 else "") + "Rs " + s


def run_demo() -> dict:
    """Runs the bundled case through the real engines and returns the results + markdown."""
    debtors = reconcile_debtors(INVOICES, RECEIPTS, SANCTION["eligible_days"], AS_OF)
    consistency = check_consistency(
        {field: [PeriodFigure(period_label=p, value=v) for p, v in hist] for field, hist in PERIODS.items()}
    )
    creditors = float(sum(a for _, a in CREDITORS))
    stock = float(PERIODS["stock_value"][-1][1])
    dp = reconcile_drawing_power(
        DrawingPowerInputs(
            sanctioned_limit=SANCTION["limit"],
            stock_margin_pct=SANCTION["stock_margin_pct"],
            debtor_margin_pct=SANCTION["debtor_margin_pct"],
            stock_value=stock,
            eligible_debtor_value=debtors.total_eligible_outstanding,
            creditor_value=creditors,
            reported_drawing_power=REPORTED_DP,
        )
    )
    headline = _headline_finding(dp)
    return {"debtors": debtors, "consistency": consistency, "dp": dp, "headline": headline,
            "markdown": _render(debtors, consistency, dp, headline, stock, creditors)}


def _render(debtors, consistency, dp, headline, stock: float, creditors: float) -> str:
    stock_part = stock * (1 - SANCTION["stock_margin_pct"] / 100)
    debtor_part = debtors.total_eligible_outstanding * (1 - SANCTION["debtor_margin_pct"] / 100)
    ineligible = [i for i in debtors.invoices if not i.eligible and i.balance > 0]
    excluded = sum(i.balance for i in ineligible)

    L: list[str] = []
    L.append(f"# KARBHARI — Working Capital Guardian\n**Demo case:** {BUSINESS} · evidence as of {AS_OF:%d %b %Y}\n")
    if dp.gap is not None and dp.gap > 0:
        L.append(f"## Potential capacity identified: **{inr(dp.gap)}**")
    L.append(
        f"Calculated Drawing Power **{inr(dp.calculated_dp)}** vs **{inr(dp.comparison_value)}** recognised by the bank, "
        f"within the sanctioned limit of {inr(SANCTION['limit'])}.\n"
    )

    L.append("### How the Drawing Power was calculated")
    L.append("| Component | Basis | Amount |\n|---|---|---:|")
    L.append(f"| Stock after margin | {inr(stock)} × (1 − {SANCTION['stock_margin_pct']:.0f}%) | {inr(stock_part)} |")
    L.append(f"| Eligible debtors after margin | {inr(debtors.total_eligible_outstanding)} × (1 − {SANCTION['debtor_margin_pct']:.0f}%) | {inr(debtor_part)} |")
    L.append(f"| Less sundry creditors | creditor ledger | −{inr(creditors)} |")
    L.append(f"| **Calculated Drawing Power** | capped at the sanctioned limit | **{inr(dp.calculated_dp)}** |")
    L.append(f"| Recognised by the bank | September stock statement | {inr(dp.comparison_value)} |")
    L.append(f"| **Gap** | | **{inr(dp.gap)}** |\n")

    L.append("### Debtors, rebuilt invoice by invoice")
    L.append(f"{len(debtors.invoices)} invoices and {len(RECEIPTS)} receipts reconciled per debtor; eligibility limit "
             f"{SANCTION['eligible_days']} days.\n")
    L.append("| Invoice | Date | Amount | Balance | Status | Age | Eligible |\n|---|---|---:|---:|---|---:|---|")
    for i in sorted(debtors.invoices, key=lambda x: x.date):
        eligible = "— (paid)" if i.balance <= 0 else ("yes" if i.eligible else "**no**")
        L.append(f"| {i.invoice_id} | {i.date:%d %b %Y} | {inr(i.amount)} | {inr(i.balance)} | {i.status} | {i.age_days} d | "
                 f"{eligible} |")
    L.append(f"\nTotal outstanding **{inr(debtors.total_outstanding)}**, of which eligible **{inr(debtors.total_eligible_outstanding)}**.")
    if debtors.duplicate_invoices:
        L.append(f"Duplicate invoices excluded: {', '.join(d.invoice_id for d in debtors.duplicate_invoices)}.")
    if debtors.unallocated_receipts:
        L.append(f"Unallocated receipts: {', '.join(r.receipt_id for r in debtors.unallocated_receipts)}.")
    L.append("")

    L.append("### Findings")
    findings = [(headline.status, headline.title, headline.amount_impact)]
    if ineligible:
        names = ", ".join(f"{i.invoice_id} ({i.age_days} days, {inr(i.balance)} open)" for i in ineligible)
        findings.append(("supported", f"Ineligible book debts past the {SANCTION['eligible_days']}-day limit: {names}", excluded))
    for f in consistency.flags:
        findings.append(("unresolved",
                         f"{f.field.replace('_', ' ').capitalize()} moved {f.pct_change:+.1f}% from {f.from_period} "
                         f"({inr(f.from_value)}) to {f.to_period} ({inr(f.to_value)}) — confirm what drove it before "
                         f"relying on the latest figure alone", None))
    for status, title, amount in findings:
        amt = f" · **{inr(amount)}**" if amount else ""
        L.append(f"- `{_STATUS_LABEL[status]}` {title}{amt}")
    L.append("")
    if dp.assumptions_used:
        L.append("**Assumptions:** " + " ".join(dp.assumptions_used) + "\n")
    L.append("_The gap is headroom that appears supportable under the supplied facility terms, within the existing "
             "sanctioned limit. It is not a request for more credit and not a guarantee the bank will release it._\n")

    L.append("---")
    L.append("**How this sandbox run works.** aiKart's sandbox accepts text only and has no LLM key, so the six bundled "
             f"documents ({', '.join(EVIDENCE)}) were transcribed into line items in advance. Everything after that — "
             "per-debtor reconciliation and ageing, the period-over-period checks, the Drawing Power calculation and the "
             "graded findings — was computed just now by KARBHARI's real deterministic engines, the same code the web app "
             "uses. In the full web app the live agent reads the uploaded files itself and decides which checks to run. "
             "The same documents through the live agent gave identical figures.")
    return "\n".join(L)
