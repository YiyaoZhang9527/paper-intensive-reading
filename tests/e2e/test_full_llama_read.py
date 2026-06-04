"""端到端测试：完整跑一篇论文的精读流程。

注意：使用 mock LLM 避免实际 API 调用。
真正的 E2E（实际下载 LLaMA PDF）作为可选 manual test。
"""
import pytest
from datetime import date

from paper_intensive_reading.pdf_parse import parse
from paper_intensive_reading.to_markdown import render_single_note
from paper_intensive_reading.formula_explainer import (
    FormulaSegment, build_empty_explanation
)
from paper_intensive_reading.paper_store import (
    init_db, add_paper, get_paper, update_status
)


@pytest.fixture
def sample_paper_with_pdf(tmp_path):
    """构造一个带 PDF 文件的 Paper 对象（用 PyMuPDF 生成）。"""
    import fitz
    pdf_path = tmp_path / "2302.13971.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "LLaMA: Open and Efficient Foundation Language Models")
    doc.new_page().insert_text(
        (50, 50),
        "Abstract\nWe introduce LLaMA, a collection of foundation models.\n\n"
        "1 Introduction\n\nFoundation models are large language models.\n\n"
        "2 Method\n\nWe use RMSNorm. Eq. (1): x = y + z.\n\n"
        "3 Experiments\n\nResults on benchmarks.\n\n"
        "Figure 1: Architecture diagram.",
    )
    doc.save(str(pdf_path))
    doc.close()

    return pdf_path


def test_full_pipeline_parse_to_note(tmp_path, sample_paper_with_pdf):
    """完整流程：PDF → Paper → 公式讲解 → Markdown。"""
    # 1. 解析 PDF
    paper = parse(sample_paper_with_pdf)
    paper.arxiv_id = "2302.13971"
    paper.published = date(2023, 2, 27)
    assert "LLaMA" in paper.title
    assert len(paper.sections) >= 1

    # 2. 构造一个 mock 公式讲解
    expl = build_empty_explanation()
    expl.arxiv_id = "2302.13971"
    expl.formula_number = "(1)"
    expl.latex = "x = y + z"
    expl.segments[1] = FormulaSegment(kind="plain", content="x 等于 y 加 z")
    expl.verified = True
    expl.verification_outputs = {
        "actual": {"ok": True, "stdout": "6"}
    }

    # 把公式归到第一个有公式的 section
    if paper.sections:
        paper.sections[0].formulas.append(
            __import__("paper_intensive_reading.types", fromlist=["Formula"]).Formula(
                number="(1)", latex="x = y + z",
                context_before="", context_after="",
            )
        )

    # 3. 渲染笔记
    user_state = {"depth_pref": "elementary"}
    md = render_single_note(paper, [expl], user_state)

    # 4. 验证产物
    assert "arxiv_id: 2302.13971" in md
    assert "LLaMA" in md
    assert "x 等于 y 加 z" in md
    assert "actual" in md.lower() or "6" in md


def test_full_pipeline_with_db_persistence(tmp_path, sample_paper_with_pdf):
    """测试 SQLite 持久化。"""
    db_path = tmp_path / "papers.sqlite"
    init_db(db_path)

    # add_paper
    add_paper(db_path, {
        "arxiv_id": "2302.13971", "title": "LLaMA",
        "authors": ["Touvron"], "affiliations": ["Meta AI"],
        "abstract": "x", "published": date(2023, 2, 27),
        "pdf_path": str(sample_paper_with_pdf),
    })

    # get_paper
    p = get_paper(db_path, "2302.13971")
    assert p is not None
    assert p["title"] == "LLaMA"
    assert p["status"] == "待读"

    # update_status
    update_status(db_path, "2302.13971", "已读完")
    p2 = get_paper(db_path, "2302.13971")
    assert p2["status"] == "已读完"
    assert p2["finished_at"] is not None
