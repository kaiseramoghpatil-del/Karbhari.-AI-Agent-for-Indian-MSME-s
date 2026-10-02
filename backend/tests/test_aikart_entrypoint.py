from app.aikart.entrypoint import run


def test_run_produces_markdown_output():
    # The aiKart sandbox input model has no file-upload field, so a run via
    # this path always has zero evidence attached -- it's exercising the
    # case -> investigation wiring, not the real document pipeline (which
    # test_guardian_live.py covers against the web app's evidence upload path).
    result = run({"message": "My bank says my credit line is fully used"})
    assert result["format"] == "markdown"
    assert "no_evidence" in result["response"]
    assert "Case created" in result["response"]


def test_run_rejects_empty_message(client):
    try:
        run({"message": "   "})
        assert False, "expected ValueError"
    except ValueError:
        pass


DEMO = "Run the bundled demo case (Suryoday Textiles, 6 documents)"


def test_demo_case_runs_real_engines_and_matches_live_agent_figures():
    from app.aikart.demo_case import run_demo

    r = run_demo()
    # Same figures the live agent produced on these six documents in the web app.
    assert r["debtors"].total_outstanding == 1_800_000
    assert r["debtors"].total_eligible_outstanding == 1_200_000
    assert r["dp"].calculated_dp == 2_570_000
    assert r["dp"].gap == 220_000
    assert r["dp"].assumptions_used == []
    assert r["headline"].status == "supported"
    assert {f.field for f in r["consistency"].flags} == {"stock_value", "sundry_debtors", "sundry_creditors"}
    ineligible = {i.invoice_id for i in r["debtors"].invoices if not i.eligible and i.balance > 0}
    assert ineligible == {"INV-1002", "INV-1005"}


def test_demo_selected_in_mode_returns_full_report():
    result = run({"mode": DEMO})
    assert result["format"] == "markdown"
    body = result["response"]
    assert "Rs 2,20,000" in body and "Rs 25,70,000" in body and "Rs 23,50,000" in body
    assert "transcribed" in body  # provenance is stated, not hidden


def test_demo_keeps_buyer_note():
    body = run({"mode": DEMO, "message": "Why is my DP low?"})["response"]
    assert body.startswith("> **Your note:** Why is my DP low?")


def test_describe_mode_keeps_original_behaviour():
    result = run({"mode": "Describe my own problem", "message": "Bank cut my limit"})
    assert "no_evidence" in result["response"]


def test_mode_with_empty_message_falls_back_to_demo():
    assert "Rs 2,20,000" in run({"mode": "Describe my own problem", "message": ""})["response"]
