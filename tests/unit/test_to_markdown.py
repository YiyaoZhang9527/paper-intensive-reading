from datetime import date
from paper_intensive_reading.to_markdown import render_single_note
from paper_intensive_reading.types import Paper, Section, Paragraph, Figure


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
        FormulaSegment, build_empty_explanation
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


class TestCompareNote:
    def test_render_compare_note(self):
        from paper_intensive_reading.to_markdown import render_compare_note
        papers = [
            Paper(arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
                  affiliations=["Meta AI"], abstract="LLaMA paper",
                  published=date(2023, 2, 27), pdf_path="/tmp/llama.pdf",
                  sections=[], figures=[], tables=[], algorithms=[], references=[]),
            Paper(arxiv_id="2005.14165", title="GPT-3", authors=["Brown"],
                  affiliations=["OpenAI"], abstract="GPT-3 paper",
                  published=date(2020, 5, 28), pdf_path="/tmp/gpt3.pdf",
                  sections=[], figures=[], tables=[], algorithms=[], references=[]),
        ]
        md = render_compare_note(papers)
        assert "LLaMA" in md
        assert "GPT-3" in md
        assert "对比" in md or "vs" in md.lower()
        assert "概览对比" in md or "维度" in md


class TestSurveyNote:
    def test_render_survey_note(self):
        from paper_intensive_reading.to_markdown import render_survey_note
        papers_info = [
            {"arxiv_id": "2302.04761", "title": "Toolformer", "authors": ["Schick"],
             "year": 2023, "reason": "开山工作", "method": "自监督构造工具调用数据",
             "citations": 1834, "url": "https://arxiv.org/abs/2302.04761"},
            {"arxiv_id": "2210.03629", "title": "ReAct", "authors": ["Yao"],
             "year": 2022, "reason": "推理+行动范式", "method": "Reason+Act 循环",
             "citations": 1521, "url": "https://arxiv.org/abs/2210.03629"},
        ]
        md = render_survey_note("LLM Agents", papers_info)
        assert "LLM Agents" in md
        assert "Toolformer" in md
        assert "ReAct" in md
        assert "阅读路径" in md
        assert "开山" in md
