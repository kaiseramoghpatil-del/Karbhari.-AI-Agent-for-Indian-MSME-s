"""
Database engine and session management (SQLite via SQLModel).

SQLite is a deliberate Phase 0 choice: zero setup, file-based, trivially
inspectable, and entirely adequate for a hackathon's case/evidence metadata
volume. Swapping to Postgres later only touches this file and config.py.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import DATABASE_URL, ensure_data_dirs

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def init_db() -> None:
    ensure_data_dirs()
    # Import models so their tables are registered on SQLModel.metadata
    # before create_all is called.
    from .models import case, evidence, investigation  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
