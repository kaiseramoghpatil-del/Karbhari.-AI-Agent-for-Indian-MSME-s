from app.reconciliation.consistency import check_consistency
from app.reconciliation.schemas import PeriodFigure


def test_large_swing_is_flagged():
    history = {
        "stock_value": [
            PeriodFigure(period_label="Aug-2026", value=3_000_000),
            PeriodFigure(period_label="Sep-2026", value=5_000_000),  # +66.7%
        ]
    }
    result = check_consistency(history, threshold_pct=20)
    assert len(result.flags) == 1
    assert result.flags[0].field == "stock_value"
    assert round(result.flags[0].pct_change, 1) == 66.7


def test_small_change_is_not_flagged():
    history = {
        "stock_value": [
            PeriodFigure(period_label="Aug-2026", value=5_000_000),
            PeriodFigure(period_label="Sep-2026", value=5_200_000),  # +4%
        ]
    }
    result = check_consistency(history, threshold_pct=20)
    assert result.flags == []


def test_single_period_is_not_flagged():
    history = {"stock_value": [PeriodFigure(period_label="Sep-2026", value=5_000_000)]}
    result = check_consistency(history, threshold_pct=20)
    assert result.flags == []


def test_zero_to_nonzero_is_flagged():
    history = {
        "creditor_value": [
            PeriodFigure(period_label="Aug-2026", value=0),
            PeriodFigure(period_label="Sep-2026", value=800_000),
        ]
    }
    result = check_consistency(history, threshold_pct=20)
    assert len(result.flags) == 1
    assert "0" in result.flags[0].message


def test_multiple_fields_checked_independently():
    history = {
        "stock_value": [
            PeriodFigure(period_label="Aug-2026", value=5_000_000),
            PeriodFigure(period_label="Sep-2026", value=5_100_000),  # +2%, not flagged
        ],
        "total_debtor_value": [
            PeriodFigure(period_label="Aug-2026", value=2_000_000),
            PeriodFigure(period_label="Sep-2026", value=4_000_000),  # +100%, flagged
        ],
    }
    result = check_consistency(history, threshold_pct=20)
    assert len(result.flags) == 1
    assert result.flags[0].field == "total_debtor_value"
