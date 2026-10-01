from app.aikart.entrypoint import run


def test_run_produces_markdown_output():
    result = run({"message": "My bank says my credit line is fully used"})
    assert result["format"] == "markdown"
    assert "not_implemented" in result["response"] or "not yet implemented" in result["response"]
    assert "Case created" in result["response"]


def test_run_rejects_empty_message(client):
    try:
        run({"message": "   "})
        assert False, "expected ValueError"
    except ValueError:
        pass
