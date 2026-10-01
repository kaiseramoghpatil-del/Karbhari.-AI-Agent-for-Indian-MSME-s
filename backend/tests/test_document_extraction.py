import io
from pathlib import Path

from openpyxl import Workbook

from app.services.document_extraction import extract_text


def _make_minimal_pdf(text: str) -> bytes:
    """Hand-built minimal single-page PDF with a correct xref table, so we
    can test the real pypdf code path without adding a PDF-generation
    dependency just for tests."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    stream = f"BT /F1 18 Tf 10 150 Td ({text}) Tj ET".encode()
    objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    return bytes(out)


def test_extract_plain_text(tmp_path: Path):
    f = tmp_path / "note.txt"
    f.write_text("Sanctioned Limit: Rs. 50,00,000", encoding="utf-8")
    assert "50,00,000" in extract_text(f, "text/plain", "note.txt")


def test_extract_csv(tmp_path: Path):
    f = tmp_path / "ledger.csv"
    f.write_text("Name,Amount\nAcme,12345\n", encoding="utf-8")
    text = extract_text(f, "text/csv", "ledger.csv")
    assert "Acme" in text and "12345" in text


def test_extract_xlsx(tmp_path: Path):
    wb = Workbook()
    ws = wb.active
    ws.append(["Item", "Value"])
    ws.append(["Stock", 500000])
    f = tmp_path / "stock.xlsx"
    wb.save(f)
    text = extract_text(f, None, "stock.xlsx")
    assert "Stock" in text and "500000" in text


def test_extract_pdf_with_real_text_layer(tmp_path: Path):
    f = tmp_path / "sanction.pdf"
    f.write_bytes(_make_minimal_pdf("Sanctioned Limit 8000000"))
    text = extract_text(f, "application/pdf", "sanction.pdf")
    assert "Sanctioned Limit 8000000" in text


def test_extract_pdf_without_text_layer_returns_clear_marker(tmp_path: Path):
    # A PDF with no page content at all (no Contents stream) -- simulates a
    # scanned image PDF with no extractable text layer.
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 300] >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()

    f = tmp_path / "scanned.pdf"
    f.write_bytes(bytes(out))
    text = extract_text(f, "application/pdf", "scanned.pdf")
    assert "No extractable text" in text


def test_malformed_file_does_not_crash(tmp_path: Path):
    f = tmp_path / "broken.pdf"
    f.write_bytes(b"not actually a pdf")
    text = extract_text(f, "application/pdf", "broken.pdf")
    assert "Could not extract text" in text


def test_missing_file_does_not_crash(tmp_path: Path):
    text = extract_text(tmp_path / "does_not_exist.txt", "text/plain", "does_not_exist.txt")
    assert "missing from storage" in text
