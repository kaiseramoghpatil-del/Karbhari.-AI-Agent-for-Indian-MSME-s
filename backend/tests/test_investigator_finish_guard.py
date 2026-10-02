"""
Investigator loop robustness, with a scripted fake LLM (no network, deterministic):
- the finish guard: a premature finish (before calculate_drawing_power has run)
  is deferred once with an explicit instruction, then accepted;
- rate limits: Gemini 429s are waited out as requested (capped and bounded),
  while other errors keep the normal retry budget.
"""

import json

from app.agent import investigator
from app.agent.investigator import FINISH_DEFERRED_NOTE, run_investigation
from app.llm.base import LLMClient, LLMError

FINISH = {"thought": "Done.", "action": "finish", "tool": None, "tool_input": None, "findings": []}
LIST = {"thought": "Inventory first.", "action": "call_tool", "tool": "list_evidence", "tool_input": {}, "findings": None}
CALC = {
    "thought": "Compute DP.",
    "action": "call_tool",
    "tool": "calculate_drawing_power",
    "tool_input": {
        "sanctioned_limit": 1_000_000,
        "stock_margin_pct": 25,
        "debtor_margin_pct": 40,
        "stock_value": 400_000,
        "eligible_debtor_value": 200_000,
        "creditor_value": 50_000,
        "reported_drawing_power": 300_000,
    },
    "findings": None,
}


class ScriptedLLM(LLMClient):
    def __init__(self, actions):
        self.actions = list(actions)
        self.prompts: list[str] = []

    def generate_json(self, system_prompt, user_prompt, *, temperature=0.2):
        self.prompts.append(user_prompt)
        return json.dumps(self.actions.pop(0))


def test_premature_finish_is_deferred_then_agent_calculates():
    llm = ScriptedLLM([LIST, FINISH, CALC, FINISH])
    run = run_investigation(llm, [])

    assert run.stopped_reason == "agent_finished"
    assert run.toolbox.last_dp_result is not None
    assert run.toolbox.last_dp_result.calculated_dp == 370_000  # 400k*0.75 + 200k*0.60 - 50k
    assert [t.tool for t in run.trace] == ["list_evidence", "finish_deferred", "calculate_drawing_power"]
    assert FINISH_DEFERRED_NOTE in llm.prompts[2]  # the model was told why


def test_second_premature_finish_is_accepted_no_loop():
    llm = ScriptedLLM([LIST, FINISH, FINISH])
    run = run_investigation(llm, [])

    assert run.stopped_reason == "agent_finished"
    assert run.toolbox.last_dp_result is None  # guardian reports it honestly
    assert [t.tool for t in run.trace] == ["list_evidence", "finish_deferred"]


def test_finish_after_calculation_is_not_deferred():
    llm = ScriptedLLM([CALC, FINISH])
    run = run_investigation(llm, [])

    assert run.stopped_reason == "agent_finished"
    assert [t.tool for t in run.trace] == ["calculate_drawing_power"]


class FlakyLLM(ScriptedLLM):
    """Raises the given errors first, then plays the scripted actions."""

    def __init__(self, errors, actions):
        super().__init__(actions)
        self.errors = list(errors)

    def generate_json(self, system_prompt, user_prompt, *, temperature=0.2):
        if self.errors:
            raise self.errors.pop(0)
        return super().generate_json(system_prompt, user_prompt, temperature=temperature)


QUOTA = LLMError('Gemini API error 429: {"error": {"code": 429, "message": "Quota exceeded. Please retry in 3.5s.", "status": "RESOURCE_EXHAUSTED"}}')


def test_rate_limit_waits_as_asked_and_completes(monkeypatch):
    sleeps = []
    monkeypatch.setattr(investigator.time, "sleep", sleeps.append)
    llm = FlakyLLM([QUOTA, QUOTA, QUOTA], [CALC, FINISH])  # 3 quota errors > normal retry budget
    run = run_investigation(llm, [])

    assert run.stopped_reason == "agent_finished"
    assert run.toolbox.last_dp_result is not None
    assert sleeps == [4.5, 4.5, 4.5]  # Gemini's "retry in 3.5s" + 1 s margin


def test_rate_limit_wait_is_capped_and_bounded(monkeypatch):
    sleeps = []
    monkeypatch.setattr(investigator.time, "sleep", sleeps.append)
    long_wait = LLMError("Gemini API error 429: RESOURCE_EXHAUSTED. Please retry in 300s.")
    llm = FlakyLLM([long_wait] * 10, [CALC, FINISH])
    run = run_investigation(llm, [])

    assert run.stopped_reason.startswith("llm_error")  # gives up eventually, never hangs
    assert max(sleeps) == investigator.RATE_LIMIT_MAX_WAIT_SECONDS


def test_other_errors_keep_the_normal_retry_budget(monkeypatch):
    sleeps = []
    monkeypatch.setattr(investigator.time, "sleep", sleeps.append)
    boom = LLMError("Gemini API error 500: internal")
    llm = FlakyLLM([boom, boom, boom], [CALC, FINISH])
    run = run_investigation(llm, [])

    assert run.stopped_reason.startswith("llm_error")
    assert sleeps == [investigator.LLM_RETRY_DELAY_SECONDS] * investigator.LLM_CALL_RETRIES


def test_mistaken_finish_tool_call_is_also_guarded():
    finish_as_tool = {"thought": "Done.", "action": "call_tool", "tool": "finish_investigation", "tool_input": {}, "findings": None}
    llm = ScriptedLLM([finish_as_tool, CALC, FINISH])
    run = run_investigation(llm, [])

    assert run.toolbox.last_dp_result is not None
    assert [t.tool for t in run.trace] == ["finish_deferred", "calculate_drawing_power"]
