"""
Points KARBHARI at an isolated, throwaway data directory for the whole test
session, set up before any `app.*` module is imported so config.py picks it
up at import time. This keeps tests from touching the developer's real
backend/data/karbhari.db or uploads.
"""

import os
import tempfile
from pathlib import Path

_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="karbhari_test_"))
os.environ["KARBHARI_DATA_DIR"] = str(_TEST_DATA_DIR)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
