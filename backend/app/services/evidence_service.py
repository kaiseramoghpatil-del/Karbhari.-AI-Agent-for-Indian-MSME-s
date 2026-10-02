"""
Evidence service layer: file storage + metadata records.

Storage is deliberately simple for Phase 0 -- files land on local disk under
UPLOAD_DIR/<case_id>/<evidence_id>_<original_filename>. That is an
abstraction boundary, not a permanent design: swapping to object storage
later only touches `_write_file`/`_delete_file` in this module, nothing
upstream (routers, aiKart entrypoint) needs to change.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlmodel import Session, select

from ..config import UPLOAD_DIR
from ..models.evidence import Evidence


def _case_dir(case_id: str) -> Path:
    d = UPLOAD_DIR / case_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_file(case_id: str, original_filename: str, content: bytes) -> tuple[str, str]:
    """Writes bytes to disk and returns (evidence_id, storage_path)."""
    evidence_id = str(uuid.uuid4())
    safe_name = Path(original_filename).name  # strip any path components
    dest = _case_dir(case_id) / f"{evidence_id}_{safe_name}"
    dest.write_bytes(content)
    # Always stored with "/" so a data directory written on Windows still
    # resolves inside the Linux Docker image (and vice versa).
    storage_path = dest.relative_to(UPLOAD_DIR).as_posix()
    return evidence_id, storage_path


def resolve_storage_path(storage_path: str) -> Path:
    """Absolute path for a stored evidence file. Accepts older records saved
    with Windows "\\" separators as well as the current "/" form."""
    return UPLOAD_DIR / storage_path.replace("\\", "/")


def _delete_file(storage_path: str) -> None:
    path = resolve_storage_path(storage_path)
    if path.exists():
        path.unlink()


def add_evidence(
    session: Session,
    case_id: str,
    original_filename: str,
    content_type: str | None,
    content: bytes,
    category: str = "other",
) -> Evidence:
    evidence_id, storage_path = _write_file(case_id, original_filename, content)
    evidence = Evidence(
        id=evidence_id,
        case_id=case_id,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=len(content),
        category=category,
        storage_path=storage_path,
    )
    session.add(evidence)
    session.commit()
    session.refresh(evidence)
    return evidence


def list_evidence(session: Session, case_id: str) -> list[Evidence]:
    return list(
        session.exec(
            select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.uploaded_at)
        )
    )


def get_evidence(session: Session, evidence_id: str) -> Evidence | None:
    return session.get(Evidence, evidence_id)


def delete_evidence(session: Session, evidence_id: str) -> bool:
    evidence = session.get(Evidence, evidence_id)
    if evidence is None:
        return False
    _delete_file(evidence.storage_path)
    session.delete(evidence)
    session.commit()
    return True
