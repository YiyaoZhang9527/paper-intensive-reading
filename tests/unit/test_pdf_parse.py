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


class TestExtractFormulas:
    def test_extract_formula_numbers(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_formulas
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "We define Loss = -sum(y * log(p)) in Eq. (1).\n"
            "The attention is QK^T / sqrt(d) in equation (2).",
        )
        doc.save(str(pdf))
        doc.close()

        formulas = extract_formulas(pdf)
        assert any(f.number == "(1)" for f in formulas)
        assert any(f.number == "(2)" for f in formulas)

    def test_no_formulas_returns_empty(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_formulas
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((50, 50), "Plain text without formulas.")
        doc.save(str(pdf))
        doc.close()

        assert extract_formulas(pdf) == []


class TestExtractFiguresTablesAlgorithms:
    def test_figure_captions(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_figure_captions
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Some text.\n\nFigure 1: Overview of our model architecture.\n\n"
            "Figure 2: Training loss curves over 100 epochs.",
        )
        doc.save(str(pdf))
        doc.close()

        captions = extract_figure_captions(pdf)
        assert len(captions) == 2
        assert "Overview" in captions[0]["caption"]

    def test_table_captions(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_tables
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Table 1: Main results on ImageNet.\nTable 2: Ablation study.",
        )
        doc.save(str(pdf))
        doc.close()

        tables = extract_tables(pdf)
        assert len(tables) == 2

    def test_algorithm_blocks(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_algorithms
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Algorithm 1: Training procedure\n"
            "1: Initialize model\n2: for epoch in range(N):\n3:    train()\n4: end for",
        )
        doc.save(str(pdf))
        doc.close()

        algos = extract_algorithms(pdf)
        assert len(algos) == 1
        assert "Training" in algos[0].title
        assert "Initialize" in algos[0].pseudocode


class TestUnifiedParse:
    def test_parse_returns_paper(self, tmp_path):
        from paper_intensive_reading.pdf_parse import parse
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Test Paper Title\n\nAbstract: We propose something.\n\n"
            "1 Introduction\n\nIntro text.\n\n"
            "2 Method\n\nEq. (1): x = y + z.\n\n"
            "Figure 1: Architecture diagram.",
        )
        doc.save(str(pdf))
        doc.close()

        paper = parse(pdf)
        assert "Test Paper" in paper.title
        assert len(paper.sections) >= 2
        assert paper.pdf_path == str(pdf)

    def test_parse_unsafe_pdf_raises(self, tmp_path):
        from paper_intensive_reading.pdf_parse import parse
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R /OpenAction 3 0 R>> endobj
2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj
3 0 obj <</S /JavaScript /JS (alert(1))>> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000106 00000 n
trailer <</Size 4 /Root 1 0 R>> startxref 160 %%EOF
"""
        pdf = tmp_path / "evil.pdf"
        pdf.write_bytes(content)

        with pytest.raises(ParseError):
            parse(pdf)
