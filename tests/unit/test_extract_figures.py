import pytest
from pathlib import Path
from paper_intensive_reading.extract_figures import (
    extract_embedded_images, render_page_region
)


def test_extract_embedded_images(tmp_path):
    import fitz
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    img = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    img.clear_with(255)
    page.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=img)
    doc.save(str(pdf))
    doc.close()

    out_dir = tmp_path / "figs"
    paths = extract_embedded_images(pdf, out_dir)
    assert len(paths) >= 1
    assert all(Path(p).exists() for p in paths)


def test_render_page_region(tmp_path):
    import fitz
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "Test page content")
    doc.save(str(pdf))
    doc.close()

    out = tmp_path / "page.png"
    render_page_region(pdf, page_num=0, out_path=out)
    assert out.exists()
    assert out.stat().st_size > 0
