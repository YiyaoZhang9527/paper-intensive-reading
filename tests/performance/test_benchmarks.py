"""性能基准：确保关键操作在合理时间内完成。"""
import time
import fitz
import pytest
from pathlib import Path
from paper_intensive_reading.pdf_parse import parse
from paper_intensive_reading.extract_figures import extract_embedded_images
from paper_intensive_reading.render_formula import render
from paper_intensive_reading.numpy_runner import run


@pytest.fixture
def synthetic_pdf(tmp_path):
    """构造一个 10 页的测试 PDF（含章节标记以便 parse 通过）。"""
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    for i in range(10):
        page = doc.new_page()
        page.insert_text((50, 50), f"{i+1} Section {i+1}\n\nContent of page {i+1}.")
    doc.save(str(pdf))
    doc.close()
    return pdf


def test_parse_under_5s(synthetic_pdf):
    start = time.time()
    parse(synthetic_pdf)
    duration = time.time() - start
    assert duration < 5, f"parse() took {duration:.2f}s, expected < 5s"


def test_extract_figures_under_10s(synthetic_pdf, tmp_path):
    out_dir = tmp_path / "figs"
    start = time.time()
    extract_embedded_images(synthetic_pdf, out_dir)
    duration = time.time() - start
    assert duration < 10, f"extract took {duration:.2f}s, expected < 10s"


def test_render_formula_under_1s(tmp_path):
    out = tmp_path / "eq.png"
    start = time.time()
    render(r"\frac{a}{b}", out_path=out)
    duration = time.time() - start
    assert duration < 1, f"render took {duration:.2f}s, expected < 1s"


def test_numpy_run_under_5s():
    code = """
import numpy as np
x = np.random.rand(100, 100)
y = x @ x.T
print(y.shape)
"""
    start = time.time()
    result = run(code, timeout=5)
    duration = time.time() - start
    assert result.ok
    assert duration < 5, f"numpy run took {duration:.2f}s, expected < 5s"


@pytest.mark.slow
def test_full_pipeline_under_3min(synthetic_pdf):
    """完整跑一篇论文（10 页）应在 3 分钟内。"""
    from paper_intensive_reading.formula_explainer import build_empty_explanation
    from paper_intensive_reading.to_markdown import render_single_note

    start = time.time()
    paper = parse(synthetic_pdf)
    expl = build_empty_explanation()
    expl.formula_number = "(1)"
    expl.latex = "x = 1"
    md = render_single_note(paper, [expl], {"depth_pref": "elementary"})
    duration = time.time() - start

    assert duration < 180, f"Full pipeline took {duration:.2f}s, expected < 180s"
    assert len(md) > 0
