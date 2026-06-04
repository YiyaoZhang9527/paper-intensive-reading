import pytest
from datetime import date
from paper_intensive_reading.to_markdown import render_single_note
from paper_intensive_reading.types import Paper, Section, Paragraph, Formula, Figure


def test_render_basic_note(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971",
        title="LLaMA: Open and Efficient Foundation Language Models",
        authors=["Touvron", "Lavril"],
        affiliations=["Meta AI"],
        abstract="We introduce LLaMA.",
        published=date(2023, 2, 27),
        pdf_path="/tmp/2302.13971.pdf",
        sections=[
            Section(number="1", title="Introduction", level=1,
                    paragraphs=[Paragraph(text="Foundation models are large.", page=1)]),
        ],
        figures=[Figure(number="Figure 1", caption="Overview", image_path="figures/fig-1.png", page=3)],
        tables=[], algorithms=[], references=[],
    )

    md = render_single_note(paper, formula_explanations=[], user_state={})

    assert "LLaMA: Open and Efficient" in md
    assert "---" in md  # front matter
    assert "arxiv_id: 2302.13971" in md
    assert "TL;DR" in md or "一句话" in md
    assert "## 1. 背景与动机" in md or "## 背景" in md
    assert "## 1. Introduction" in md or "## Introduction" in md
    assert "Figure 1" in md


def test_render_with_formula_explanations(tmp_path):
    from paper_intensive_reading.formula_explainer import (
        FormulaExplanation, FormulaSegment, build_empty_explanation
    )
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf",
        sections=[Section(number="3", title="Method", level=1, paragraphs=[])],
        figures=[], tables=[], algorithms=[], references=[],
    )
    expl = build_empty_explanation()
    expl.arxiv_id = "2302.13971"
    expl.formula_number = "(1)"
    expl.latex = "E = mc^2"
    expl.segments[1] = FormulaSegment(kind="plain", content="能量等于质量乘光速平方")

    md = render_single_note(paper, formula_explanations=[expl], user_state={})
    assert "公式 (1)" in md or "Eq. (1)" in md
    assert "能量等于质量" in md


def test_render_with_glossary(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    md = render_single_note(paper, formula_explanations=[], user_state={}, glossary=["attention", "embedding"])
    assert "术语表" in md
    assert "attention" in md.lower() or "注意力" in md


def test_render_includes_front_matter(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    md = render_single_note(paper, formula_explanations=[], user_state={}, status="已读完", tags=["llm"])
    assert "status: 已读完" in md
    assert "tags:" in md
