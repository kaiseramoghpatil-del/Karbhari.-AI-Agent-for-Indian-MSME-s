# KARBHARI — Working Capital Guardian

**Phase 1: real investigation.** KARBHARI now takes a real evidence bundle
(sanction letter, stock statement, debtor/creditor ledgers, bank statement —
PDF, XLSX, CSV, or plain text) and produces an actual, evidence-backed
investigation: it extracts facts from messy documents, deterministically
reconciles Drawing Power against the sanction terms, and synthesizes graded
findings (supported / unresolved / ineligible-contradicted) with citations
back to source evidence. See **Phase 1 results** below for a real run.

## What's real vs. stubbed

| Layer | Status |
|---|---|
| Case create/list/get, evidence upload/list/delete | Real (Phase 0) |
| Document text extraction (PDF, XLSX, CSV, plain text) | Real |
| LLM fact extraction from messy documents, with provenance quotes | Real (Gemini, provider-swappable) |
| Deterministic Drawing Power reconciliation | Real — pure Python, no LLM arithmetic |
| Graded findings (supported/unresolved/ineligible-contradicted) with evidence citations | Real |
| aiKart sandbox entrypoint | Real, calls the same service layer as the web app (text-only input, no evidence upload — see Known limitations) |
| Docker image | Built and verified (Phase 0) |
| Multi-document conflict resolution across contradictory evidence | Detected and recorded (`AggregatedFacts.conflicts`), not yet surfaced as its own finding type |
| TReDS/banking API integration, autonomous actions, multi-agent orchestration | Not built — out of scope for Phase 1 |

## Architecture

```
karbhari/
  backend/
    app/
      main.py                 FastAPI app; serves API + built frontend
      config.py                env-driven paths (data dir, db)
      db.py                     SQLite engine/session (SQLModel)
      models/                   Case, Evidence, Investigation (SQLModel tables)
      services/
        case_service.py
        evidence_service.py
        investigation_service.py
        document_extraction.py  PDF/XLSX/CSV/text -> plain text, never raises
      llm/
        base.py                 LLMClient interface -- agent code depends only on this
        gemini_client.py         Gemini REST implementation (no SDK dependency)
        factory.py               LLM_PROVIDER-driven; only "gemini" implemented today
      agent/
        schemas.py               ExtractedFacts, Finding, ReconciliationResult, etc.
        prompts.py                extraction + findings-synthesis system prompts
        guardian.py               WorkingCapitalGuardian -- the real pipeline (see below)
      calculations/
        drawing_power.py          deterministic DP formula -- the ONLY place that number is computed
      routers/                    thin FastAPI route handlers calling services/
      aikart/entrypoint.py        aiKart "Try Me Now" sandbox adapter -- calls services/, not a separate app
    tests/                       pytest suite, including one live Gemini integration test
    data/                        sqlite db + uploaded evidence files (gitignored)
  frontend/                      Vite + React + TypeScript
    src/pages/                    CaseListPage, CaseWorkspacePage (Evidence / Investigation / Findings / Actions tabs)
    src/components/                ReconciliationCard, FindingsList, EvidenceUploader/List
  Dockerfile                    multi-stage: builds frontend, copies into the backend image
  agent-manifest.yaml           aiKart manifest (image reference is a placeholder)
```

### The investigation pipeline

```
evidence files
  -> document_extraction (deterministic: bytes -> plain text)
  -> LLM Stage 1 "extraction" (one call, all documents): reads messy text,
     returns structured facts per document, each with a verbatim quote
  -> aggregation (deterministic): one value per field across documents,
     preferring the expected document type, recording any conflicts
  -> calculations/drawing_power.py (deterministic): computes Drawing Power
     from the sanction terms and records, compares against what the bank
     reports, produces the headline gap figure
  -> headline finding (deterministic, built directly from the reconciliation
     result -- the LLM never sees or touches this number)
  -> LLM Stage 2 "findings synthesis" (one call): given the extracted facts
     AND the deterministic reconciliation as ground truth, produces
     additional graded findings (data-quality issues, ambiguities,
     anything that undermines a favorable conclusion) with citations
```

**"The LLM reasons, code calculates"** is enforced structurally, not just by
prompt instruction: the headline capacity-gap finding is constructed in
Python directly from `ReconciliationResult` (`guardian.py::_headline_finding`)
before the LLM is ever asked to produce findings. The LLM's Stage 2 call is
told the number as a given fact and instructed never to recompute it; it can
only add *additional* findings around it.

**Why two LLM calls, not one per document:** sending all documents in one
extraction call (rather than N calls) keeps this within free-tier rate
limits and is simpler to orchestrate, while still giving the model full
context across documents to catch things like stale/mismatched dates. A
richer pipeline (e.g. per-document calls, or an agent that decides what
evidence to request next) is a reasonable Phase 2 direction, not a Phase 1
requirement.

**Provider-agnostic LLM layer:** `agent/` code only imports from `llm/base.py`.
Today `llm/factory.py` only implements Gemini (REST, no SDK dependency), but
adding another provider means writing one more class and a branch in the
factory — nothing in `agent/` or `calculations/` changes. Configure via
`LLM_PROVIDER` / `LLM_MODEL` in `.env`.

**Why SQLite / why a JSON details column:** unchanged from Phase 0 — zero
setup, adequate for hackathon volume. `Investigation.details_json` holds the
full structured pipeline output (extractions, aggregated facts, reconciliation,
findings) as one JSON blob rather than new normalized tables, since the shape
is still likely to change in Phase 2.

## Phase 1 results (real run, not illustrative)

A 5-document synthetic evidence bundle was built with a deliberate, hand-
computed discrepancy and run through the actual pipeline end-to-end:

- Sanction letter: ₹80,00,000 limit, 25% stock margin, 40% debtor margin, 90-day debtor eligibility
- Stock statement (XLSX): ₹50,00,000, dated 15-May-2026
- Debtor ledger (CSV): ₹40,00,000 total, ₹30,00,000 eligible (<90 days)
- Creditor ledger (CSV): ₹8,00,000
- Bank statement: reported Drawing Power ₹46,00,000

Expected calculation: `50,00,000×0.75 + 30,00,000×0.60 − 8,00,000 = 47,50,000`,
against a reported ₹46,00,000 → gap of **₹1,50,000**.

**Actual result:** extraction correctly pulled every figure with accurate
quotes from all 5 documents (PDF path tested separately — see Known
limitations); aggregation found zero conflicts and zero missing fields;
the deterministic calculator produced **exactly** ₹47,50,000 / gap ₹1,50,000,
matching the hand-computed expectation precisely. The LLM's findings-synthesis
stage additionally flagged, entirely on its own, that the stock statement
(May 2026) was dated ~4.5 months before the other records (September 2026) —
correctly citing the sanction letter's own 3-month staleness rule and all 4
relevant evidence IDs — something that would be easy for a reviewer to miss
without a side-by-side date comparison.

One real bug was found and fixed during this process: Gemini occasionally
embeds literal unescaped newline/tab characters inside quoted JSON string
values, which Python's strict JSON parser rejects. Fixed by parsing with
`json.loads(..., strict=False)` and logging (rather than silently
swallowing) any genuine parse failure.

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
Open the URL Vite prints (defaults to `http://127.0.0.1:5173`). The dev
server proxies `/api/*` to `http://127.0.0.1:8000` (see `vite.config.ts`).

> **Windows note:** Vite's default dev-server host can bind to the IPv6
> loopback (`::1`) only, which makes `127.0.0.1` unreachable even though
> the server reports "ready". `vite.config.ts` pins `server.host` to
> `127.0.0.1` to avoid this.

**Tests:**
```bash
cd backend
.venv/Scripts/python -m pytest -q
```
21 tests, including one live test against the real Gemini API
(`test_guardian_live.py`) — it auto-skips if `GOOGLE_API_KEY` isn't set, so
the rest of the suite stays runnable offline/in CI.

## aiKart sandbox entrypoint (local test, no Docker needed)

```bash
cd backend
AIKART_INPUT='{"message":"My bank says my credit line is fully used but I think there is unused capacity"}' python -m app.aikart.entrypoint
```
Outside the real sandbox there's no `/aikart/` directory to write to, so
`main()` fails at the final file-write step with a clear `FileNotFoundError`
— expected on a dev machine. Call the pure function directly to check the
actual logic (this is what the test suite does):
```python
from app.aikart.entrypoint import run
run({"message": "..."})
```

## Docker

```bash
docker build -t karbhari:0.1.0 .
docker run -p 8000:8000 karbhari:0.1.0
```
Built and verified against Docker 29.8.1 in Phase 0; the Phase 1 code
changes don't affect the container setup (same dependencies install path,
same entrypoints). Re-verify with a fresh build before relying on it for
submission, since this hasn't been rebuilt since the Phase 1 changes landed.

To exercise the aiKart sandbox path in the built image:
```bash
mkdir -p aikart_test
echo '{"message":"My bank says my credit line is fully used"}' > aikart_test/input.json

docker run --rm -v "$(pwd)/aikart_test:/aikart" \
  --entrypoint python karbhari:0.1.0 -m app.aikart.entrypoint

cat aikart_test/output.json
```

## aiKart manifest

`agent-manifest.yaml` is written against the aiKart Agent Manifest guide,
but **`runtime.image` is a placeholder** (`docker.io/REPLACE_ME/karbhari:0.1.0`).
Before actually submitting: build and push the image to a public registry,
then replace the `image` field with that reference.

## Known limitations of this phase (by design or by honest gap, not hidden)

- **PDF extraction is unit-tested, not live-tested end-to-end.** The live
  Phase 1 run used a sanction letter as plain text (realistic PDFs in
  production are often scanned images needing OCR, which is out of scope).
  `test_document_extraction.py` verifies the real pypdf code path against a
  hand-built PDF with a genuine text layer, and separately verifies graceful
  handling of a PDF with no text layer and of malformed files — but no run
  has yet put a real-world PDF sanction letter through the full pipeline.
- **The aiKart sandbox can't exercise evidence upload** — its input types
  are text/textarea/number/boolean/select only, no file upload (unchanged
  from Phase 0). The full document pipeline only runs through the web app.
- **Cross-document conflicts are detected but not yet a finding.** If two
  documents disagree on a figure, `AggregatedFacts.conflicts` records both
  values, and the LLM's findings stage *can* see and act on this (it's part
  of the payload it receives), but there's no guaranteed dedicated finding
  for it yet — worth confirming behavior with a deliberately conflicting
  test case in Phase 2.
- **Single evidence bundle tested.** One rich, deliberately-constructed
  scenario was verified end-to-end. Edge cases not yet tried: documents in
  a language other than English, truly illegible/corrupted uploads, a case
  with 10+ documents, or genuinely contradictory source documents.
- No authentication — anyone who can reach the API can see every case.
- Evidence categories are advisory, not enforced.

## What Phase 2 might plug into

- A `Finding` type/key for cross-document conflicts specifically, rather
  than relying on the LLM to notice `AggregatedFacts.conflicts` unprompted.
- Real-world PDF testing (scanned-image OCR is a bigger, separate decision).
- The "Actions" tab — currently still a placeholder; the natural next step
  once findings exist is turning the capacity-gap finding into a concrete
  next action (e.g. a draft note to the bank requesting DP recomputation).
- Persisting the investigation pipeline's shape as normalized tables instead
  of one JSON blob, once the shape stabilizes.
