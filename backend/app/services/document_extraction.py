"""
Raw text extraction from evidence files.

This module's only job is bytes-on-disk -> plain text. It never interprets
meaning (that is the LLM's job) and never fails loudly -- an unreadable or
unsupported file returns a clear marker string so the rest of the pipeline
can treat it as "nothing extracted" rather than crashing the investigation.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from openpyxl import load_workbook
from pypdf import PdfReader

MAX_CHARS = 20_000  # keep individual-document text bounded for prompt size


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    return text[:MAX_CHARS] + f"\n...[truncated, {len(text) - MAX_CHARS} more characters]"


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        return "[No extractable text found -- this PDF may be a scanned image without a text layer.]"
    return text


def _extract_xlsx(data: bytes) -> str:
    wb = load_workbook(io.BytesIO(data), data_only=True)
    parts = []
    for sheet in wb.worksheets:
        parts.append(f"--- Sheet: {sheet.title} ---")
        for row in sheet.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                parts.append("\t".join("" if c is None else str(c) for c in row))
    return "\n".join(parts).strip() or "[Spreadsheet appears empty.]"


def _extract_csv(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    return "\n".join("\t".join(row) for row in reader).strip() or "[CSV appears empty.]"


def _extract_plain_text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace").strip() or "[File appears empty.]"


def extract_text(file_path: Path, content_type: str | None, original_filename: str) -> str:
    """
    Best-effort plain-text extraction. Dispatches on file extension first
    (more reliable than browser-supplied content_type), falls back to
    content_type, then to a plain-text decode attempt.
    """
    if not file_path.exists():
        return "[Evidence file is missing from storage.]"

    data = file_path.read_bytes()
    suffix = Path(original_filename).suffix.lower()

    try:
        if suffix == ".pdf" or content_type == "application/pdf":
            text = _extract_pdf(data)
        elif suffix in (".xlsx", ".xlsm"):
            text = _extract_xlsx(data)
        elif suffix == ".csv":
            text = _extract_csv(data)
        else:
            text = _extract_plain_text(data)
    except Exception as exc:  # noqa: BLE001
        return f"[Could not extract text from this file: {exc}]"

    return _truncate(text)
