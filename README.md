# KARBHARI — Working Capital Guardian

**P2: a real bounded investigation, not a fixed pipeline.** KARBHARI now runs
an actual agent loop: it decides what evidence to read, independently
reconstructs debtor eligibility from invoice/receipt-level records (not a
ledger's own subtotal), checks period-over-period consistency, and only then
computes Drawing Power — deterministically, never by LLM arithmetic. See
**P2 verified results** below for a real run against a 7-document case.

## What's real vs. stubbed

| Layer | Status |
|---|---|
| Case/evidence CRUD, document text extraction (PDF/XLSX/CSV/text) | Real (P0/P1) |
| Bounded ReAct-style investigator loop (agent chooses tools, not a fixed script) | Real |
| Deterministic debtor reconciliation (FIFO receipt allocation, per-debtor segregation, duplicate/unallocated detection, ageing/eligibility) | Real — pure Python, independently tested |
| Deterministic period-over-period consistency checking | Real — pure Python |
| Deterministic Drawing Power calculation, with eligible-debtor figure forcibly overridden by the real reconciliation (not the agent's own number) | Real |
| Graded findings (supported/unresolved/ineligible-contradicted) with evidence citations | Real |
| Full tool-call trace (for demo narration / "how did it find that") | Real, surfaced in the UI |
| aiKart sandbox entrypoint | Real, text-only input (no evidence upload — unchanged limitation from P0) |
| Docker image | Built and verified against P1 code; **not rebuilt against P2** — rebuild before relying on it |
| TReDS/banking APIs, autonomous actions, multi-agent orchestration, OCR | Not built — deliberately out of scope |

## Architecture

```
karbhari/
  backend/app/
    reconciliation/
      schemas.py              Invoice, Receipt, DebtorReconciliationResult, ConsistencyResult
      debtor_reconciliation.py  FIFO allocation, per-debtor segregation, duplicate/unallocated detection
      consistency.py            period-over-period variance flagging
    calculations/
      drawing_power.py          the DP formula -- the ONLY place that number is computed
    llm/                        provider-agnostic LLMClient (Gemini REST today)
    agent/
      tools.py                  InvestigatorToolbox -- the tool catalog + executors
      investigator.py           the bounded ReAct loop (max 20 steps)
      guardian.py                public entry point; builds the deterministic headline
                                 finding and a code-level consistency-coverage backstop
      prompts.py                single investigator system prompt (checklist-style)
    ...                         (routers/, models/, services/ unchanged from P0/P1)
```

### The investigation loop

```
list_evidence
  -> read_evidence (agent decides which documents, in what order)
  -> reconcile_debtors   (deterministic -- agent supplies parsed invoice/receipt
                           line items, the tool does FIFO allocation, ageing,
                           duplicate/unallocated detection, PER DEBTOR)
  -> check_consistency   (deterministic -- flags >20% period-over-period swings)
  -> calculate_drawing_power (deterministic -- eligible_debtor_value is forcibly
                               overridden by reconcile_debtors' output if one was
                               run, regardless of what the agent passes in)
  -> finish (agent-authored findings for everything EXCEPT the headline gap,
             which guardian.py constructs directly from the DP tool's own output)
```

Bounded at 20 tool calls. Every step is logged (thought, tool, input, output)
into `Investigation.details.tool_trace` and rendered in the UI's "How it
investigated" tab — this is the actual trace of what happened, not a
reconstruction after the fact.

**"The LLM reasons, Python calculates" is enforced in code, not just prompted
for:**
- The headline Drawing Power gap finding is built by `guardian.py` directly
  from `calculate_drawing_power`'s return value. The agent never computes or
  restates this number.
- `calculate_drawing_power`'s tool executor *overrides* whatever
  `eligible_debtor_value` the agent supplies with the real reconciled figure
  from `reconcile_debtors`, if one was run in this session — see
  `tools.py::_calculate_drawing_power`. Tested directly
  (`test_agent_tools.py`).
- `reconcile_debtors` groups invoices/receipts by `debtor_name` internally
  before any matching happens, so correctness does not depend on the agent
  remembering to call it once per debtor — a real bug found during demo-case
  construction (see below) is now a permanent regression test.

## P2 verified results (real run, not illustrative)

A 7-document evidence bundle for "Suryoday Textiles Pvt Ltd" was built with
genuine complexity, and the TRUE expected results were hand-computed
independently *before* running the agent:
- A real PDF sanction letter (₹80L limit, 25%/40% margins, 90-day debtor
  eligibility, 3-month stock-statement staleness rule)
- Two stock statement periods (Aug ₹42L → Sep ₹58L, a deliberate +38.1% swing)
- 9 invoices across 5 debtors, including one duplicate ledger row
- 4 receipts, including one tagged-partial, one untagged (FIFO-allocated),
  and one that overpays and leaves an unallocated balance
- A creditor ledger and a bank statement (reported DP ₹32L)

**Hand-computed ground truth:** eligible debtor outstanding ₹16,00,000;
calculated DP = ₹58L×0.75 + ₹16L×0.60 − ₹9L = **₹44,10,000**; gap vs. reported
= **₹12,10,000**.

**Actual agent run (live, Gemini, 11 tool calls):** matched every figure
exactly — ₹16,00,000 eligible debtors, ₹44,10,000 calculated DP, ₹12,10,000
gap. The agent independently: excluded the duplicate invoice (₹3,50,000),
flagged the ₹70,000 unallocated receipt, excluded a 105-day-old invoice as
ineligible, and caught the +38.1% stock swing via `check_consistency` —
5 findings total, correctly split across supported/unresolved/
ineligible-contradicted, not one-sided.

### Real bugs found and fixed during this verification (not hypothetical)

1. **Multi-debtor FIFO bleed.** `reconcile_debtors`, as first written, didn't
   segregate by debtor — a parallel build of the demo case independently
   discovered that pooling multiple debtors' records in one call let one
   debtor's untagged receipt pay off a *different* debtor's older invoice.
   Fixed by grouping internally by `debtor_name` before matching.
   Regression-tested (`test_untagged_receipts_do_not_bleed_across_debtors`).
2. **`finish_investigation` tool-call ambiguity.** Listing it in the same
   numbered catalog as real tools made the model try to invoke it via
   `action: call_tool` instead of the special `action: finish`. Fixed the
   prompt *and* added a code-level fallback that treats the mistaken call as
   a finish rather than wasting a step on an error.
3. **Intermittent Gemini `MALFORMED_RESPONSE`** and a **corrupted-token JSON
   prefix** (a stray non-ASCII character before an otherwise valid JSON
   object) — both observed directly in logs, not theoretical. Both are now
   retried (API errors and parse failures share one retry budget) before a
   step is given up on.
4. **Step budget too low.** 10 steps wasn't enough for a 7-document case
   (list + 7 reads + 3 tool calls = 11 minimum). Raised to 20.
5. **`check_consistency` is unreliably invoked by the agent.** Across 6 live
   runs, 4 different prompt strategies (prose instruction, "MANDATORY"
   framing, an explicit ordered checklist) and a model upgrade attempt, the
   agent called `check_consistency` in only 1 of 6 runs despite it clearly
   applying. This is a genuine, reproducible agent-autonomy limitation, not
   fully solved. Mitigated — not fixed — with a code-level backstop
   (`guardian.py::_consistency_coverage_gap`): if the agent never calls it
   but the evidence has multiple same-category items, a `Finding` is added
   stating plainly that the check wasn't run, rather than silently omitting
   coverage. See **Known limitations**.

## Running locally

Requires Python 3.12+ and Node 20+, and a Google AI Studio API key (free
tier) in `backend/.env` — see `backend/.env.example`.

**Backend:**
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev
```

> **Windows dev-server note:** `uvicorn --reload` has not reliably picked up
> every code change during iterative testing on this machine — if behavior
> doesn't match what you expect after an edit, kill all python processes and
> start a fresh instance rather than trusting `--reload`.

**Tests:**
```bash
cd backend
.venv/Scripts/python -m pytest -q
```
41 tests, including one live test against the real Gemini API
(auto-skips without `GOOGLE_API_KEY`).

## Docker

Built and verified in P0/P1; **has not been rebuilt against the P2 agent
loop / reconciliation modules**. Rebuild (`docker build -t karbhari:0.3.0 .`)
and re-run the verification steps from the P1 README section before relying
on it for submission.

## Known limitations (stated honestly, not hidden)

- **`check_consistency` is not reliably invoked by the agent** (see above).
  The code-level backstop guarantees the *gap in coverage* is always visible
  in the findings, but does not guarantee the check itself runs every time.
  A model capable of more reliable instruction-following, or native
  function-calling with enforced tool sequencing, would likely close this;
  neither was adopted here to keep the integration surface and risk bounded
  for a hackathon timeline.
- **Creditor-side reconciliation stays simple** (a single total, no
  invoice/payment-level AP reconciliation) — a deliberate scope cut, not an
  oversight.
- **Cross-document conflicts** (two documents disagreeing on the same figure)
  are not explicitly tested in the P2 demo case — the aggregation-level
  conflict detection from P1 was removed when the fixed extraction pipeline
  was replaced by the agent loop; nothing currently re-implements it.
- **Single demo case family verified.** Six live runs of one well-understood
  7-document case, not a range of case shapes (10+ documents, contradictory
  evidence, non-English text, genuinely illegible uploads).
- The aiKart sandbox still cannot exercise evidence upload (unchanged from
  P0/P1 — its input schema has no file type).
- No authentication. Evidence categories are advisory, not enforced.

## What's next

- Either accept the `check_consistency` coverage gap as a known constraint of
  the current model tier, or invest in native function-calling / a stronger
  model specifically to close it.
- Rebuild and re-verify the Docker image against P2 before submission.
- The "Actions" tab is still a placeholder — turning the capacity-gap finding
  into a concrete next action (e.g. a draft note to the bank) is the natural
  next increment once the investigation layer is trusted.
- Re-test with a deliberately harder case (contradictory documents, more
  debtors, a genuinely illegible upload) to find the next real failure mode
  before a judge does.
