# KARBHARI — Working Capital Guardian

**Phase 0: application foundation.** This phase does not implement the real
investigation — it builds the chassis (case → evidence → investigation →
findings → actions) that later phases plug real reasoning into.

## What's real vs. stubbed in Phase 0

| Layer | Status |
|---|---|
| Case create/list/get | Real |
| Evidence upload/list/delete (metadata + file storage) | Real |
| `Run investigation` button | Real pipeline, honest stub result — no reasoning, no invented numbers |
| Working Capital Guardian agent | Interface defined (`backend/app/agent/guardian.py`), not implemented |
| aiKart sandbox entrypoint | Real, calls the same service layer as the web app |
| Docker image | **Built and verified** — container runs the full case/evidence/investigate flow, serves the frontend, and the aiKart sandbox entrypoint works via volume-mounted `/aikart` |

## Architecture

```
karbhari/
  backend/
    app/
      main.py            FastAPI app; serves API + built frontend
      config.py           env-driven paths (data dir, db)
      db.py                SQLite engine/session (SQLModel)
      models/              Case, Evidence, Investigation (SQLModel tables)
      services/            case_service, evidence_service, investigation_service
                            — plain functions, no FastAPI imports, so both
                            the HTTP routers and the aiKart entrypoint call
                            the exact same code
      routers/              thin FastAPI route handlers calling services/
      agent/guardian.py     WorkingCapitalGuardian — stub, honest about what it doesn't do yet
      aikart/entrypoint.py  aiKart "Try Me Now" sandbox adapter — calls services/, not a separate app
    tests/                 pytest suite against an isolated temp DB
    data/                   sqlite db + uploaded evidence files (gitignored)
  frontend/                 Vite + React + TypeScript
    src/pages/               CaseListPage, CaseWorkspacePage (Evidence / Investigation / Findings / Actions tabs)
    src/api/client.ts        typed fetch wrapper
  Dockerfile                multi-stage: builds frontend, copies into the backend image
  agent-manifest.yaml       aiKart manifest (image reference is a placeholder — see below)
```

**Why this split:** the aiKart sandbox contract (read `/aikart/input.json`,
write `/aikart/output.json`, one-shot, text-only inputs) is fundamentally
different from the interactive web app, but both need to produce
investigations the same way. Keeping `services/` and `agent/` free of
FastAPI-specific code means `backend/app/aikart/entrypoint.py` calls
`case_service.create_case(...)` and `investigation_service.run_investigation(...)`
directly — the same functions the HTTP routes call. There is one
implementation of KARBHARI's logic, with two thin adapters (HTTP routes,
aiKart script) in front of it.

**Why SQLite:** zero setup, file-based, trivially inspectable, entirely
adequate for a hackathon's case/evidence volume. Swapping to Postgres later
only touches `config.py` and `db.py`.

**Why a `status` field on every model:** `Evidence.status` and
`Investigation.status` exist now (`uploaded`/`not_implemented` today) so
Phase 1's parsing and reasoning pipelines have somewhere to report progress
into without a schema migration.

## Running locally

Requires Python 3.12+ and Node 20+.

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
> `127.0.0.1` to avoid this — if you change that config, keep an explicit
> host rather than leaving it to the default.

**Tests:**
```bash
cd backend
.venv/Scripts/python -m pytest -q
```

## aiKart sandbox entrypoint (local test, no Docker needed)

```bash
cd backend
AIKART_INPUT='{"message":"My bank says my credit line is fully used but I think there is unused capacity"}' python -m app.aikart.entrypoint
```
Outside the real sandbox there's no `/aikart/` directory to write to, so
`main()` will fail at the final file-write step with a clear `FileNotFoundError`
— that's expected on a dev machine. To check the actual logic without that
path, call the pure function directly (this is what the test suite does):
```python
from app.aikart.entrypoint import run
run({"message": "..."})
```

## Docker

```bash
docker build -t karbhari:0.1.0 .
docker run -p 8000:8000 karbhari:0.1.0
```

**Verified** (Docker 29.8.1): image builds clean, container serves the
frontend and API together on port 8000, and the full case → evidence →
investigate flow works against the running container, including the
uploaded file actually persisting on disk inside the container.

To exercise the aiKart sandbox path in the built image — mount a host
directory at `/aikart` containing `input.json`, matching exactly how the
real sandbox runner behaves, and override the command the same way
`agent-manifest.yaml` does:
```bash
mkdir -p aikart_test
echo '{"message":"My bank says my credit line is fully used"}' > aikart_test/input.json

docker run --rm -v "$(pwd)/aikart_test:/aikart" \
  --entrypoint python karbhari:0.1.0 -m app.aikart.entrypoint

cat aikart_test/output.json
```
This was run end-to-end: exit code 0, and `output.json` contained the
correctly-shaped `{"format": "markdown", "response": "..."}` from the same
`WorkingCapitalGuardian` stub the web app uses.

## aiKart manifest

`agent-manifest.yaml` is written against the aiKart Agent Manifest guide,
but **`runtime.image` is a placeholder** (`docker.io/REPLACE_ME/karbhari:0.1.0`).
Before actually submitting:
1. Build and push the image to a public registry.
2. Replace the `image` field with that reference.

## What Phase 1 plugs into

- `backend/app/agent/guardian.py` — replace `WorkingCapitalGuardian.investigate()`'s
  stub body with real reconciliation logic (sanction terms vs. stock/debtor/
  creditor records vs. ledger).
- `Evidence.status` — wire a parsing pipeline that moves it through
  `uploaded → parsing → parsed/failed`.
- `Investigation` — Phase 1 will want a richer result shape (graded
  findings: supported / unresolved / contradicted) rather than a single
  `summary` string; the `status`/`summary` fields can stay as a top-line
  rollup if a separate `Finding` model is introduced.
- Frontend's "Findings" and "Actions" tabs are placeholder text — they
  render real content once the agent produces it.

## Known limitations of this phase (by design, not oversight)

- No authentication — anyone who can reach the API can see every case.
- No real file parsing — uploaded PDFs/spreadsheets are stored as opaque
  bytes with metadata only.
- Evidence categories are advisory, not enforced.
- The web app and the aiKart sandbox diverge in one place: the sandbox has
  no file-upload input type (per the aiKart manifest spec), so it only
  exercises case creation + the investigation stub on a text description,
  not evidence upload. The full workflow is exercised through the web app.
