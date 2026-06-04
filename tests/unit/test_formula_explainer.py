import pytest
from paper_intensive_reading.formula_explainer import (
    FormulaExplanation, FormulaSegment, ExplanationContext,
    build_empty_explanation, FORMULA_PROMPT_TEMPLATE
)
from paper_intensive_reading.types import Formula


def test_formula_segment_creation():
    seg = FormulaSegment(
        kind="original",
        content=r"\text{RMSNorm}(x) = \frac{x}{\sqrt{\text{Mean}(x^2)}} \cdot \gamma",
    )
    assert seg.kind == "original"


def test_formula_explanation_6_segments():
    expl = build_empty_explanation()
    assert len(expl.segments) == 6
    assert [s.kind for s in expl.segments] == [
        "original", "plain", "symbols", "analogy", "example", "code"
    ]


def test_formula_explanation_to_dict():
    expl = build_empty_explanation()
    d = expl.to_dict()
    assert "segments" in d
    assert len(d["segments"]) == 6
    assert d["arxiv_id"] == ""


def test_explanation_context_depth_preference():
    ctx = ExplanationContext(arxiv_id="2302.13971", depth_pref="elementary")
    assert ctx.depth_pref == "elementary"


def test_prompt_template_has_6_placeholders():
    template = FORMULA_PROMPT_TEMPLATE
    for i in range(1, 7):
        assert f"{{SEGMENT_{i}}}" in template or f"段 {i}" in template
