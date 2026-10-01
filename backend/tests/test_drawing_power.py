from app.agent.schemas import AggregatedFacts
from app.calculations.drawing_power import reconcile_drawing_power


def test_full_data_finds_a_gap():
    facts = AggregatedFacts(
        sanctioned_limit=1_000_000,
        stock_margin_pct=25,
        debtor_margin_pct=40,
        stock_value=600_000,
        eligible_debtor_value=500_000,
        creditor_value=50_000,
        reported_drawing_power=500_000,
    )
    result = reconcile_drawing_power(facts)
    assert result.can_calculate is True
    assert result.calculated_dp == 700_000.0
    assert result.gap == 200_000.0
    assert result.assumptions_used == []


def test_missing_margins_uses_flagged_defaults():
    facts = AggregatedFacts(
        sanctioned_limit=1_000_000,
        stock_value=600_000,
        total_debtor_value=500_000,
        reported_drawing_power=400_000,
    )
    result = reconcile_drawing_power(facts)
    assert result.can_calculate is True
    assert len(result.assumptions_used) >= 2  # stock margin + debtor margin defaults
    assert any("stand-in for eligible debtor value" in a for a in result.assumptions_used)


def test_missing_critical_input_cannot_calculate():
    facts = AggregatedFacts(stock_value=600_000)
    result = reconcile_drawing_power(facts)
    assert result.can_calculate is False
    assert result.calculated_dp is None
    assert result.assumptions_used == []  # no spurious assumptions when nothing was computed
    assert any("sanctioned_limit" in m for m in result.missing_inputs)


def test_negative_gap_is_reported_honestly_not_hidden():
    """The system must not be blindly favorable to the MSME -- if the business
    is already drawing beyond what the records support, that's a negative gap,
    not a suppressed finding."""
    facts = AggregatedFacts(
        sanctioned_limit=1_000_000,
        stock_margin_pct=25,
        debtor_margin_pct=40,
        stock_value=200_000,
        eligible_debtor_value=100_000,
        creditor_value=10_000,
        reported_drawing_power=300_000,
    )
    result = reconcile_drawing_power(facts)
    assert result.can_calculate is True
    assert result.gap < 0


def test_sanctioned_limit_caps_the_calculation():
    facts = AggregatedFacts(
        sanctioned_limit=500_000,
        stock_margin_pct=25,
        debtor_margin_pct=40,
        stock_value=2_000_000,
        eligible_debtor_value=2_000_000,
        creditor_value=0,
        reported_drawing_power=400_000,
    )
    result = reconcile_drawing_power(facts)
    assert result.calculated_dp == 500_000.0  # capped, not the raw collateral-based figure
    assert any("exceeded the sanctioned limit" in a for a in result.assumptions_used)


def test_immaterial_gap_is_treated_as_zero():
    facts = AggregatedFacts(
        sanctioned_limit=1_000_000,
        stock_margin_pct=25,
        debtor_margin_pct=40,
        stock_value=600_000,
        eligible_debtor_value=500_000,
        creditor_value=50_000,
        reported_drawing_power=699_999.5,  # within MATERIALITY_THRESHOLD of 700,000
    )
    result = reconcile_drawing_power(facts)
    assert result.gap == 0.0
