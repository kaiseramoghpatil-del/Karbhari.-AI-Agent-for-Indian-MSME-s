"""
Bounded ReAct-style investigation loop.

Each turn: the model sees a transcript of everything done so far and
returns exactly one action -- call a tool, or finish. This replaces
Phase 1's fixed two-call pipeline (extract-everything, then
synthesize-findings) with an agent that actually decides what to look at
and when it has enough, bounded by MAX_STEPS so cost/runtime stay
predictable regardless of what the model decides to do.
"""

from __future__ import annotations

import json
import logging
import re
import time

from ..llm.base import LLMClient, LLMError
from ..models.evidence import Evidence
from .prompts import INVESTIGATOR_SYSTEM_PROMPT
from .schemas import Finding, ToolCallRecord
from .tools import InvestigatorToolbox

logger = logging.getLogger(__name__)

MAX_STEPS = 20
# Gemini occasionally returns an empty/MALFORMED_RESPONSE candidate under
# JSON-mode constraints for no evident reason tied to the prompt content --
# observed directly during testing. A short bounded retry absorbs that
# without masking a genuine, persistent failure (which still surfaces as
# llm_error after retries are exhausted).
LLM_CALL_RETRIES = 2
LLM_RETRY_DELAY_SECONDS = 1.5
# Gemini's free tier allows ~15 requests/minute and answers 429 with
# "Please retry in Ns". Those waits are honoured (capped) and don't consume
# LLM_CALL_RETRIES, so a busy minute slows a run down instead of failing it.
RATE_LIMIT_RETRIES = 4
RATE_LIMIT_MAX_WAIT_SECONDS = 45.0
RATE_LIMIT_DEFAULT_WAIT_SECONDS = 20.0
VALID_TOOLS = {
    "list_evidence",
    "read_evidence",
    "reconcile_debtors",
    "check_consistency",
    "calculate_drawing_power",
}
# Observed in live runs: the model sometimes finishes after reconciling debtors
# but before ever calling calculate_drawing_power, leaving the headline empty.
# The first premature finish is deferred with an explicit instruction; a second
# one is accepted (guardian.py then reports the missing calculation honestly),
# so the guard can never loop or invent a number.
FINISH_DEFERRALS = 1
FINISH_DEFERRED_NOTE = (
    "You tried to finish, but calculate_drawing_power has not been called yet. Call "
    "calculate_drawing_power now with the facility terms and figures you have read "
    "(pass null for anything you could not find; the tool reports what is missing). "
    "Then finish."
)


class InvestigationRun:
    """Result of running the loop: the full trace plus whatever the agent
    concluded, and the toolbox (so the caller can read back the last
    deterministic reconciliation/consistency/DP results directly rather
    than re-parsing them out of the trace)."""

    def __init__(self, trace: list[ToolCallRecord], findings: list[Finding], stopped_reason: str, toolbox: InvestigatorToolbox):
        self.trace = trace
        self.findings = findings
        self.stopped_reason = stopped_reason
        self.toolbox = toolbox


def run_investigation(llm: LLMClient, evidence: list[Evidence]) -> InvestigationRun:
    toolbox = InvestigatorToolbox(evidence)
    trace: list[ToolCallRecord] = []
    transcript_steps: list[dict] = []  # internal, carries full tool_output for prompt building
    deferrals_left = FINISH_DEFERRALS

    def defer_finish(step: int, thought: str) -> bool:
        """True if this finish should be deferred (and records why, visibly)."""
        nonlocal deferrals_left
        if toolbox.last_dp_result is not None or deferrals_left <= 0 or step >= MAX_STEPS:
            return False
        deferrals_left -= 1
        trace.append(
            ToolCallRecord(
                step=step,
                thought=thought,
                tool="finish_deferred",
                output_summary="Finish deferred: calculate_drawing_power had not been run yet.",
            )
        )
        transcript_steps.append({"thought": thought, "note": FINISH_DEFERRED_NOTE})
        return True

    for step in range(1, MAX_STEPS + 1):
        user_prompt = _build_transcript_prompt(transcript_steps)
        action = None
        last_exc: LLMError | None = None
        last_raw: str | None = None
        # A single retry budget covers both failure modes seen in practice:
        # the API call itself erroring (LLMError), and the API call
        # succeeding but returning text that isn't valid JSON even after
        # lenient recovery. Both are transient per-call issues, not signs
        # the investigation itself is broken -- worth one more try before
        # giving up.
        attempt = 0
        rate_limit_waits = 0
        while attempt < LLM_CALL_RETRIES + 1:
            attempt += 1
            try:
                raw = llm.generate_json(INVESTIGATOR_SYSTEM_PROMPT, user_prompt, temperature=0.15)
            except LLMError as exc:
                last_exc = exc
                # Free-tier quota (429) asks the caller to wait ~15-20 s; honour
                # that instead of burning the normal retry budget in 1.5 s steps.
                wait = _rate_limit_wait(exc)
                if wait is not None and rate_limit_waits < RATE_LIMIT_RETRIES:
                    rate_limit_waits += 1
                    attempt -= 1
                    logger.warning("Rate limited at step %s; waiting %.0f s before retrying.", step, wait)
                    time.sleep(wait)
                    continue
                logger.warning(
                    "Investigator LLM call failed at step %s, attempt %s: %s", step, attempt, exc
                )
                if attempt <= LLM_CALL_RETRIES:
                    time.sleep(LLM_RETRY_DELAY_SECONDS)
                continue

            last_raw = raw
            action = _parse_action(raw)
            if action is not None:
                break
            logger.warning(
                "Could not parse investigator action at step %s, attempt %s: %r",
                step, attempt, raw[:300],
            )
            if attempt <= LLM_CALL_RETRIES:
                time.sleep(LLM_RETRY_DELAY_SECONDS)

        if action is None and last_raw is None:
            return InvestigationRun(trace, [], f"llm_error: {last_exc}", toolbox)
        if action is None:
            return InvestigationRun(trace, [], "unparseable_action", toolbox)

        thought = str(action.get("thought", ""))

        if action.get("action") == "finish":
            if defer_finish(step, thought):
                continue
            findings = _parse_findings(action.get("findings") or [])
            return InvestigationRun(trace, findings, "agent_finished", toolbox)

        if action.get("action") == "call_tool":
            tool = action.get("tool")
            tool_input = action.get("tool_input") or {}

            # Defensive: despite the prompt saying finish_investigation is not
            # a callable tool, a model can still call it as one (observed
            # during testing). Treat it as a finish rather than burning a
            # step on an error -- the prompt instruction alone wasn't
            # reliable enough, so the code doesn't depend on it being.
            if tool == "finish_investigation":
                if defer_finish(step, thought):
                    continue
                findings = _parse_findings((tool_input or {}).get("findings") or [])
                return InvestigationRun(trace, findings, "agent_finished", toolbox)

            if tool not in VALID_TOOLS:
                logger.warning("Investigator requested unknown tool %r at step %s", tool, step)
                tool_output, summary = {"error": f"Unknown tool {tool!r}"}, "Unknown tool requested."
            else:
                tool_output, summary = toolbox.execute(tool, tool_input)

            record = ToolCallRecord(
                step=step,
                thought=thought,
                tool=str(tool),
                tool_input=tool_input,
                tool_output=tool_output,
                output_summary=summary,
            )
            trace.append(record)
            transcript_steps.append(
                {"thought": thought, "tool": tool, "tool_input": tool_input, "tool_output": tool_output}
            )
            continue

        logger.warning("Investigator returned neither call_tool nor finish at step %s: %r", step, action)
        return InvestigationRun(trace, [], "invalid_action", toolbox)

    logger.warning("Investigator hit the %s-step limit without finishing.", MAX_STEPS)
    return InvestigationRun(trace, [], "step_limit_reached", toolbox)


def _build_transcript_prompt(steps: list[dict]) -> str:
    if not steps:
        return "This is the start of the investigation. Call your first tool."

    parts = ["Here is the investigation transcript so far:\n"]
    for i, s in enumerate(steps, start=1):
        if "note" in s:
            parts.append(f"--- Step {i} ---\nYour thought: {s['thought']}\nSystem note: {s['note']}\n")
            continue
        parts.append(
            f"--- Step {i} ---\n"
            f"Your thought: {s['thought']}\n"
            f"Tool called: {s['tool']}\n"
            f"Tool input: {json.dumps(s['tool_input'])}\n"
            f"Tool output: {json.dumps(s['tool_output'], default=str)}\n"
        )
    parts.append(
        "\nDecide your next action: call another tool, or finish_investigation if you have "
        "enough to conclude."
    )
    return "\n".join(parts)


def _rate_limit_wait(exc: LLMError) -> float | None:
    """Seconds to wait if `exc` is a rate-limit (429) error, else None."""
    text = str(exc)
    if "429" not in text and "RESOURCE_EXHAUSTED" not in text:
        return None
    match = re.search(r"retry in ([\d.]+)\s*s", text)
    wait = float(match.group(1)) + 1.0 if match else RATE_LIMIT_DEFAULT_WAIT_SECONDS
    return min(wait, RATE_LIMIT_MAX_WAIT_SECONDS)


def _parse_action(raw: str) -> dict | None:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        parsed = json.loads(text, strict=False)
    except json.JSONDecodeError:
        # Observed directly during testing: Gemini can prefix the response
        # with a few corrupted/garbage characters before an otherwise valid
        # JSON object (e.g. a stray non-ASCII token). Recover by slicing to
        # the outermost braces rather than giving up outright -- this is a
        # narrow, specific recovery (not a general "guess the JSON" parser),
        # so it still fails honestly if the braces themselves are broken.
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(text[start : end + 1], strict=False)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "Failed to parse investigator JSON even after brace recovery (%s). "
                    "First 500 chars: %r", exc, text[:500]
                )
                return None
        else:
            logger.warning("Failed to parse investigator JSON (no braces found). First 500 chars: %r", text[:500])
            return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def _parse_findings(raw_findings: list) -> list[Finding]:
    findings = []
    for item in raw_findings:
        try:
            findings.append(Finding.model_validate(item))
        except Exception:  # noqa: BLE001
            continue
    return findings
