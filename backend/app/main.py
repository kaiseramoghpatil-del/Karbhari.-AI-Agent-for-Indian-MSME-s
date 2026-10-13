from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import os

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

# Restrict CORS to allowed origins to prevent unauthorized access.
# Defaults to local Vite development servers.
allowed_origins = os.environ.get(
    "KARBHARI_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(investigation.router)

# Serve the built frontend (if present) so the same container/process works
# as the whole product in Docker, without a separate frontend server.
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
