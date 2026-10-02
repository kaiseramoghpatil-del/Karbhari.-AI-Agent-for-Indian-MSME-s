from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402

from .db import init_db  # noqa: E402
from .routers import cases, evidence, health, investigation  # noqa: E402

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="KARBHARI — Working Capital Guardian", lifespan=lifespan)

# Permissive CORS for local development (the Vite dev server runs on a
# different port than the API). Tightening this is a pre-production task,
# not a Phase 0 concern.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(investigation.router)

# Serve the built frontend (if present) so the same container/process works
# as the whole product in Docker/aiKart, without a separate frontend server.
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")
    _DIST_ROOT = FRONTEND_DIST.resolve()

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        # Root-level build files (favicon.svg, favicon.png, ...) are served as
        # themselves; every other path falls back to the SPA's index.html.
        # The resolved path must stay inside dist, so "../" can't escape it.
        candidate = (_DIST_ROOT / full_path).resolve()
        if full_path and candidate.is_file() and candidate.is_relative_to(_DIST_ROOT):
            return FileResponse(candidate)
        return FileResponse(_DIST_ROOT / "index.html")
