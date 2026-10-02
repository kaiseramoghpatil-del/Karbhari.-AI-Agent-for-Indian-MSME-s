"""
Evidence storage paths are portable between Windows and the Linux Docker image:
new records use "/" and older Windows-written records ("\\") still resolve.
"""

from app.agent.tools import InvestigatorToolbox
from app.config import UPLOAD_DIR
from app.models.evidence import Evidence
from app.services.evidence_service import _write_file, resolve_storage_path


def test_new_storage_paths_use_forward_slashes():
    _, storage_path = _write_file("case-paths", "sanction.txt", b"limit")
    assert "\\" not in storage_path
    assert storage_path.startswith("case-paths/")
    assert resolve_storage_path(storage_path).read_bytes() == b"limit"


def test_windows_style_paths_still_resolve():
    assert resolve_storage_path("case-x\\file.pdf") == UPLOAD_DIR / "case-x" / "file.pdf"


def test_agent_reads_evidence_saved_with_windows_separators():
    folder = UPLOAD_DIR / "case-win"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "note.txt").write_text("Sanctioned Limit: Rs. 50,00,000", encoding="utf-8")
    ev = Evidence(
        id="ev-win",
        case_id="case-win",
        original_filename="note.txt",
        content_type="text/plain",
        size_bytes=31,
        category="sanction_letter",
        storage_path="case-win\\note.txt",
    )
    read, _ = InvestigatorToolbox(evidence=[ev]).execute("read_evidence", {"evidence_id": "ev-win"})
    assert "50,00,000" in read["text"]
