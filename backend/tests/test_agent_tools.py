"""
Direct, LLM-free tests of InvestigatorToolbox -- in particular the
calculate_drawing_power override: once reconcile_debtors has run, its
independently-reconstructed eligible-debtor figure must win regardless of
whatever the agent passes in, since that's the concrete code-level
enforcement of "the LLM reasons, Python calculates."
"""

from app.agent.tools import InvestigatorToolbox


def test_reconcile_debtors_overrides_agent_supplied_eligible_value():
    toolbox = InvestigatorToolbox(evidence=[])

    # Agent reconciles real invoice/receipt data -> true eligible total is 3,000.
    toolbox.execute(
        "reconcile_debtors",
        {
            "invoices": [{"invoice_id": "INV1", "date": "2026-09-01", "amount": 3000}],
            "receipts": [],
            "eligible_aging_days": 90,
            "as_of": "2026-09-28",
        },
    )
    assert toolbox.last_debtor_reconciliation.total_eligible_outstanding == 3000

    # Agent then (wrongly, or from a stale read) claims eligible_debtor_value=9999.
    output, summary = toolbox.execute(
        "calculate_drawing_power",
        {
            "sanctioned_limit": 100_000,
            "stock_margin_pct": 25,
            "debtor_margin_pct": 40,
            "stock_value": 10_000,
            "eligible_debtor_value": 9999,  # should be ignored
            "creditor_value": 0,
            "reported_drawing_power": 5_000,
        },
    )

    # 10,000*0.75 + 3,000*0.60 - 0 = 9,300 -- using the RECONCILED figure, not 9999.
    assert output["calculated_dp"] == 9300.0
    assert any("overridden" in a for a in output["assumptions_used"])


def test_calculate_drawing_power_without_prior_reconciliation_uses_agent_value():
    toolbox = InvestigatorToolbox(evidence=[])
    output, _ = toolbox.execute(
        "calculate_drawing_power",
        {
            "sanctioned_limit": 100_000,
            "stock_margin_pct": 25,
            "debtor_margin_pct": 40,
            "stock_value": 10_000,
            "eligible_debtor_value": 5_000,
            "creditor_value": 0,
        },
    )
    # No reconcile_debtors call happened -- nothing to override with, so the
    # agent-supplied figure is used as-is.
    assert output["calculated_dp"] == 10_000 * 0.75 + 5_000 * 0.60
    assert not any("overridden" in a for a in output["assumptions_used"])


def test_list_and_read_evidence_tools(tmp_path):
    from app.models.evidence import Evidence

    f = tmp_path / "note.txt"
    f.write_text("Sanctioned Limit: Rs. 50,00,000", encoding="utf-8")

    # storage_path is relative to UPLOAD_DIR in real use; patch UPLOAD_DIR-relative
    # resolution by pointing storage_path at an absolute-looking path isn't how the
    # real app works, so instead exercise this via the config's UPLOAD_DIR directly.
    import app.config as config

    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    real_path = config.UPLOAD_DIR / "test_note.txt"
    real_path.write_text("Sanctioned Limit: Rs. 50,00,000", encoding="utf-8")

    ev = Evidence(
        id="ev1",
        case_id="case1",
        original_filename="note.txt",
        content_type="text/plain",
        size_bytes=real_path.stat().st_size,
        category="other",
        storage_path="test_note.txt",
    )
    toolbox = InvestigatorToolbox(evidence=[ev])

    listed, _ = toolbox.execute("list_evidence", {})
    assert listed["evidence"][0]["evidence_id"] == "ev1"

    read, _ = toolbox.execute("read_evidence", {"evidence_id": "ev1"})
    assert "50,00,000" in read["text"]

    real_path.unlink()


def test_unknown_tool_returns_error_not_exception():
    toolbox = InvestigatorToolbox(evidence=[])
    output, summary = toolbox.execute("not_a_real_tool", {})
    assert "error" in output
