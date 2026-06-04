import pytest
from pathlib import Path
from paper_intensive_reading.pdf_parse import check_pdf_safety, extract_metadata
from paper_intensive_reading.errors import ParseError


def _make_minimal_pdf(tmp_path: Path, with_js: bool = False) -> Path:
    if with_js:
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R /OpenAction 3 0 R>> endobj
2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj
3 0 obj <</S /JavaScript /JS (app.alert('hacked'))>> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000106 00000 n
trailer <</Size 4 /Root 1 0 R>> startxref 160 %%EOF
"""
    else:
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>> endobj
4 0 obj <</Length 44>> stream
BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
0000000178 00000 n
trailer <</Size 5 /Root 1 0 R>> startxref 270 %%EOF
"""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(content)
    return pdf_path


class TestPdfSafety:
    def test_safe_pdf(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path, with_js=False)
        check_pdf_safety(pdf)

    def test_pdf_with_js_rejected(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path, with_js=True)
        with pytest.raises(ParseError) as exc:
            check_pdf_safety(pdf)
        assert exc.value.subtype == "dangerous"

    def test_nonexistent_raises(self, tmp_path):
        with pytest.raises(ParseError):
            check_pdf_safety(tmp_path / "missing.pdf")


class TestExtractMetadata:
    def test_basic_metadata(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path)
        meta = extract_metadata(pdf)
        assert "title" in meta
        assert "authors" in meta
        assert isinstance(meta["authors"], list)


class TestExtractSections:
    def test_recognizes_standard_sections(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_sections
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        for page_text in [
            "Title\n\nAbstract content here.",
            "1 Introduction\n\nThis is the intro.",
            "2 Method\n\nOur method is great.",
            "2.1 Submethod\n\nDetails.",
            "3 Experiments\n\nResults are good.",
        ]:
            page = doc.new_page()
            page.insert_text((50, 50), page_text)
        doc.save(str(pdf))
        doc.close()

        sections = extract_sections(pdf)
        titles = [s.title for s in sections]
        assert any("Introduction" in t for t in titles)
        assert any("Method" in t for t in titles)
        assert any("Experiments" in t for t in titles)

    def test_section_numbers(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_sections
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((50, 50), "1 Introduction\n\nBody")
        doc.new_page().insert_text((50, 50), "2.1 Sub\n\nBody")
        doc.save(str(pdf))
        doc.close()

        sections = extract_sections(pdf)
        assert any(s.number == "1" for s in sections)
        assert any(s.number == "2.1" for s in sections)
