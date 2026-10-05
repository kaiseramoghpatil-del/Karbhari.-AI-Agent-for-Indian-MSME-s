"""
Central configuration for KARBHARI.

Kept deliberately small for Phase 0: just enough settings for the database
location and where uploaded evidence files are stored on disk, both
overridable via environment variables so the same code works unchanged in
local dev and Docker.
"""

from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("KARBHARI_DATA_DIR", BACKEND_DIR / "data"))
UPLOAD_DIR = DATA_DIR / "uploads"
DB_PATH = DATA_DIR / "karbhari.db"

DATABASE_URL = os.environ.get("KARBHARI_DATABASE_URL", f"sqlite:///{DB_PATH}")


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
