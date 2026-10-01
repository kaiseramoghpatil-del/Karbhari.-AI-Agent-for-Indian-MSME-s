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
