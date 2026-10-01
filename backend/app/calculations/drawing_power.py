"""
Deterministic Drawing Power (DP) calculation.

Standard formula for a stock/debtor-hypothecated cash credit facility:

    DP = stock_value * (1 - stock_margin%) + eligible_debtor_value * (1 - debtor_margin%) - creditor_value

...capped at the sanctioned limit (a borrower can never draw more than the
bank sanctioned, no matter how large the collateral). This module is the
ONLY place that number gets computed -- the LLM is given the result and
told to treat it as ground truth, never to recompute it (see
agent/guardian.py and agent/prompts.py).

This is deliberately conservative about silently filling gaps: every
assumption made because an input was missing is recorded in
`assumptions_used` so the finding built from this result can say exactly
what it is and isn't sure about.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# NOTE: calculations/ is the foundational layer -- it defines its own I/O
# types and must never import from agent/. agent/schemas.py re-exports
# ReconciliationResult from here instead, keeping the dependency direction
# the right way round (agent depends on calculations, not vice versa).


class DrawingPowerInputs(BaseModel):
    sanctioned_limit: float | None = None
    stock_margin_pct: float | None = None
    debtor_margin_pct: float | None = None
    stock_value: float | None = None
    eligible_debtor_value: float | None = None
    total_debtor_value: float | None = None
    creditor_value: float | None = None
    reported_drawing_power: float | None = None
    current_outstanding_or_utilization: float | None = None


class ReconciliationResult(BaseModel):
    calculated_dp: float | None = None
    comparison_basis: Literal["reported_drawing_power", "current_outstanding", "none"] = "none"
    comparison_value: float | None = None
    gap: float | None = None
    assumptions_used: list[str] = Field(default_factory=list)
    missing_inputs: list[str] = Field(default_factory=list)
    can_calculate: bool = False

# Commonly-cited typical margins for stock/book-debt hypothecation in India
# (see Phase 0 research). These are fallbacks, not facts -- using them is
# always recorded in assumptions_used, never presented as extracted from
# the case's own sanction letter.
DEFAULT_STOCK_MARGIN_PCT = 25.0
DEFAULT_DEBTOR_MARGIN_PCT = 40.0

# A gap smaller than this (in absolute rupees) is treated as noise, not a
# finding -- avoids manufacturing a "discrepancy" out of rounding.
MATERIALITY_THRESHOLD = 1000.0


def reconcile_drawing_power(facts: DrawingPowerInputs) -> ReconciliationResult:
    assumptions: list[str] = []
    missing: list[str] = []

    if facts.sanctioned_limit is None:
        missing.append("sanctioned_limit (from the sanction letter)")
    if facts.stock_value is None:
        missing.append("stock_value (from a current stock statement)")

    eligible_debtor_value = facts.eligible_debtor_value
    if eligible_debtor_value is None and facts.total_debtor_value is None:
        missing.append("eligible_debtor_value or total_debtor_value (from a debtor ledger)")

    can_calculate = not missing

    if not can_calculate:
        # Don't record margin/creditor assumptions for a calculation that
        # never runs -- that would misleadingly imply work was done.
        return ReconciliationResult(
            calculated_dp=None,
            comparison_basis="none",
            comparison_value=None,
            gap=None,
            assumptions_used=[],
            missing_inputs=missing,
            can_calculate=False,
        )

    if eligible_debtor_value is None:
        eligible_debtor_value = facts.total_debtor_value
        assumptions.append(
            "No debtor ageing breakdown was found, so total debtor value was used as a "
            "stand-in for eligible debtor value. This likely OVERSTATES eligible debtors "
            "-- treat the calculated figure as an upper bound, not a precise one."
        )

    if facts.stock_margin_pct is not None:
        stock_margin_pct = facts.stock_margin_pct
    else:
        stock_margin_pct = DEFAULT_STOCK_MARGIN_PCT
        assumptions.append(
            f"No stock margin was found in the sanction terms -- used the typical "
            f"{DEFAULT_STOCK_MARGIN_PCT:.0f}% as a placeholder. Confirm the actual "
            f"sanctioned margin before relying on this figure."
        )

    if facts.debtor_margin_pct is not None:
        debtor_margin_pct = facts.debtor_margin_pct
    else:
        debtor_margin_pct = DEFAULT_DEBTOR_MARGIN_PCT
        assumptions.append(
            f"No book-debt margin was found in the sanction terms -- used the typical "
            f"{DEFAULT_DEBTOR_MARGIN_PCT:.0f}% as a placeholder. Confirm the actual "
            f"sanctioned margin before relying on this figure."
        )

    creditor_value = facts.creditor_value
    if creditor_value is None:
        creditor_value = 0.0
        if facts.stock_value is not None or eligible_debtor_value is not None:
            assumptions.append(
                "No sundry creditor figure was found -- treated as zero. Omitting "
                "creditors always OVERSTATES drawing power, so this calculation is "
                "optimistic until a creditor ledger is supplied."
            )

    stock_component = facts.stock_value * (1 - stock_margin_pct / 100)
    debtor_component = eligible_debtor_value * (1 - debtor_margin_pct / 100)
    raw_dp = stock_component + debtor_component - creditor_value
    calculated_dp = max(0.0, min(raw_dp, facts.sanctioned_limit))

    if raw_dp > facts.sanctioned_limit:
        assumptions.append(
            "The uncapped collateral-based figure exceeded the sanctioned limit; the "
            "sanctioned limit is the hard ceiling regardless of collateral value."
        )

    comparison_basis: str = "none"
    comparison_value: float | None = None
    if facts.reported_drawing_power is not None:
        comparison_basis = "reported_drawing_power"
        comparison_value = facts.reported_drawing_power
    elif facts.current_outstanding_or_utilization is not None:
        comparison_basis = "current_outstanding"
        comparison_value = facts.current_outstanding_or_utilization
    else:
        missing.append(
            "reported_drawing_power or current_outstanding_or_utilization "
            "(from a bank/CC account statement) -- cannot compare the calculated "
            "figure against anything without this."
        )

    gap = None
    if comparison_value is not None:
        gap = calculated_dp - comparison_value
        if abs(gap) < MATERIALITY_THRESHOLD:
            gap = 0.0

    return ReconciliationResult(
        calculated_dp=round(calculated_dp, 2),
        comparison_basis=comparison_basis,  # type: ignore[arg-type]
        comparison_value=comparison_value,
        gap=round(gap, 2) if gap is not None else None,
        assumptions_used=assumptions,
        missing_inputs=missing,
        can_calculate=True,
    )
