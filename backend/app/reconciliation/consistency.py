"""
Period-over-period consistency checking.

Deterministic and deliberately narrow: it flags a large swing between two
periods' figures for the same field (stock value, debtor total, etc.) --
it does not and cannot explain *why* the swing happened. That's exactly
the kind of judgment call left to the investigating agent, which sees the
flag alongside the rest of the evidence and can reason about plausible
causes (seasonal demand, a data error, genuine business growth).
"""

from __future__ import annotations

from .schemas import ConsistencyResult, PeriodFigure, VarianceFlag

DEFAULT_THRESHOLD_PCT = 20.0


def check_consistency(
    field_history: dict[str, list[PeriodFigure]],
    threshold_pct: float = DEFAULT_THRESHOLD_PCT,
) -> ConsistencyResult:
    """
    field_history: field name -> chronologically ordered PeriodFigure list
    (caller is responsible for ordering; this module doesn't guess dates
    from labels).
    """
    flags: list[VarianceFlag] = []

    for field, periods in field_history.items():
        if len(periods) < 2:
            continue
        for prev, curr in zip(periods, periods[1:]):
            if prev.value == 0:
                if curr.value != 0:
                    flags.append(
                        VarianceFlag(
                            field=field,
                            from_period=prev.period_label,
                            to_period=curr.period_label,
                            from_value=prev.value,
                            to_value=curr.value,
                            pct_change=float("inf"),
                            message=(
                                f"{field.replace('_', ' ')} went from 0 in {prev.period_label} "
                                f"to {curr.value} in {curr.period_label} -- confirm this is a "
                                f"genuine new balance, not a missing prior-period record."
                            ),
                        )
                    )
                continue

            pct_change = (curr.value - prev.value) / prev.value * 100
            if abs(pct_change) >= threshold_pct:
                flags.append(
                    VarianceFlag(
                        field=field,
                        from_period=prev.period_label,
                        to_period=curr.period_label,
                        from_value=prev.value,
                        to_value=curr.value,
                        pct_change=round(pct_change, 1),
                        message=(
                            f"{field.replace('_', ' ')} changed {pct_change:+.1f}% from "
                            f"{prev.period_label} ({prev.value}) to {curr.period_label} "
                            f"({curr.value}) -- worth confirming what drove this before "
                            f"relying on the latest figure alone."
                        ),
                    )
                )

    return ConsistencyResult(flags=flags)
