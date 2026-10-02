"""
Entrypoint for aiKart's "Try Me Now" sandbox (Method 1 submission).

This script is the aiKart-side adapter, not a second implementation of
KARBHARI. It reads the buyer's input, then calls the exact same
case_service / investigation_service functions the FastAPI routers use, and
formats the result as the markdown aiKart expects. If Phase 1+ changes how
an investigation is produced, this file does not need to change.

Per the aiKart Agent Manifest guide:
  - buyer input arrives as a JSON object at /aikart/input.json (or the
    AIKART_INPUT env var)
  - the result must be written to /aikart/output.json as
    {"format": "...", "response": "..."}
  - the manifest's inputs[] only support text/textarea/number/boolean/select
    fields (no file upload). By default the `mode` select runs the bundled
    demo case (see demo_case.py) through the real deterministic engines;
    "Describe my own problem" creates a case from the text alone. The full
    evidence-upload workflow with the live agent runs in the web app.
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from ..db import get_session, init_db  # noqa: E402
from ..models.case import CaseCreate  # noqa: E402
from ..services import case_service, investigation_service  # noqa: E402
from .demo_case import run_demo  # noqa: E402

DEMO_MODE_PREFIX = "Run the bundled demo case"

INPUT_PATH = "/aikart/input.json"
OUTPUT_PATH = "/aikart/output.json"


def read_input() -> dict:
    if os.path.exists(INPUT_PATH):
        with open(INPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raw = os.environ.get("AIKART_INPUT")
    if raw:
        return json.loads(raw)
    raise RuntimeError("No input found at /aikart/input.json or AIKART_INPUT")


def wants_demo(payload: dict) -> bool:
    """Demo when the buyer picks it in the `mode` select, or leaves the description empty
    while a mode was supplied. A bare `message` with no `mode` keeps the original behaviour."""
    mode = str(payload.get("mode") or "")
    if mode.startswith(DEMO_MODE_PREFIX):
        return True
    return bool(mode) and not (payload.get("message") or "").strip()


def run(payload: dict) -> dict:
    """Pure function (no filesystem I/O) so this is directly unit-testable."""
    if wants_demo(payload):
        response = run_demo()["markdown"]
        message = (payload.get("message") or "").strip()
        if message:
            response = f"> **Your note:** {message}\n\n" + response
        return {"format": "markdown", "response": response}

    message = (payload.get("message") or "").strip()
    if not message:
        raise ValueError("input.json must include a non-empty 'message' field (or choose the demo case)")

    init_db()
    session_gen = get_session()
    session = next(session_gen)
    try:
        case = case_service.create_case(
            session, CaseCreate(name=message[:80], business_name=None)
        )
        investigation = investigation_service.run_investigation(session, case)
        # Read everything we need while the session is still open --
        # SQLModel/SQLAlchemy expires attributes on commit by default, so
        # touching these objects after the session closes below would raise.
        case_name = case.name
        investigation_status = investigation.status
        investigation_summary = investigation.summary
    finally:
        session_gen.close()

    response = (
        f"**Case created:** {case_name}\n\n"
        f"**Status:** {investigation_status}\n\n"
        f"{investigation_summary}\n\n"
        "_This aiKart sandbox run has no evidence attached because its input fields are "
        "text-only -- no file upload. The full investigation (document extraction, "
        "Drawing Power reconciliation, graded findings) runs when evidence is attached "
        "through the web app. To see a full investigation here, choose the bundled demo case._"
    )
    return {"format": "markdown", "response": response}


def main() -> int:
    try:
        payload = read_input()
        output = run(payload)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"KARBHARI sandbox run failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
