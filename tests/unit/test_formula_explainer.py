from paper_intensive_reading.formula_explainer import (
    FormulaSegment, ExplanationContext,
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


class TestParseSegments:
    def test_parse_6_segments(self):
        from paper_intensive_reading.formula_explainer import parse_llm_response

        llm_output = """## 段 1
\\text{Attention}(Q,K,V) = \\text{softmax}(\\frac{QK^\\top}{\\sqrt{d_k}})V
## 段 2
每个词看其他词的相关度，加权汇总。
## 段 3
Q (Query, 第5层): 查询向量
K (Key, 第5层): 键向量
## 段 4
图书馆查资料。
## 段 5
d=4 例子: ...
## 段 6
import numpy as np
x = 1
"""

        segments = parse_llm_response(llm_output)
        assert len(segments) == 6
        assert "softmax" in segments[0].content
        assert "图书馆" in segments[3].content
        assert "import numpy" in segments[5].content

    def test_parse_with_extra_text(self):
        from paper_intensive_reading.formula_explainer import parse_llm_response

        llm_output = """前面有一些废话。

## 段 1
公式
## 段 2
白话
## 段 3
符号
## 段 4
类比
## 段 5
例子
## 段 6
代码

后面也有废话。
"""
        segments = parse_llm_response(llm_output)
        assert len(segments) == 6


class TestCallLlm:
    def test_call_llm_with_mock(self, monkeypatch):
        from paper_intensive_reading import formula_explainer
        from paper_intensive_reading.formula_explainer import explain_formula

        def mock_llm(prompt, **kwargs):
            return """## 段 1
E = mc^2
## 段 2
能量等于质量乘光速平方
## 段 3
E (能量, 第0层)
## 段 4
像烧煤释放能量
## 段 5
m=1, c=2 → E=4
## 段 6
import numpy as np
print(1 * 2**2)
"""

        monkeypatch.setattr(formula_explainer, "call_llm", mock_llm)

        formula = Formula(
            number="(1)", latex="E = mc^2",
            context_before="Einstein", context_after="rest energy",
        )
        expl = explain_formula(formula, arxiv_id="test", llm_fn=mock_llm)
        assert len(expl.segments) == 6
        assert "mc^2" in expl.segments[0].content
        assert expl.verified is False


class TestVerifyWithNumpy:
    def test_verify_runs_code(self):
        from paper_intensive_reading.formula_explainer import verify_code_segment

        code = """
import numpy as np
Q = np.array([[1, 0, 1, 0]])
K = np.array([[1, 1, 0, 0]])
scores = Q @ K.T
print(f"scores = {scores}")
"""
        result = verify_code_segment(code)
        assert result["ok"]
        assert "scores" in result["stdout"]

    def test_verify_handles_failure(self):
        from paper_intensive_reading.formula_explainer import verify_code_segment

        code = "import os\nos.system('echo HACKED')"
        result = verify_code_segment(code)
        assert not result["ok"]

    def test_extract_code_from_segment(self):
        from paper_intensive_reading.formula_explainer import extract_code

        segment_content = """
**NumPy 代码 + 实际运行**：

```python
import numpy as np
x = np.array([1, 2, 3])
print(x.sum())
```

实际跑出：
```
6
```
"""
        code = extract_code(segment_content)
        assert "import numpy" in code
        assert "x.sum()" in code


class TestThreeWayVerification:
    def test_run_three_way_verification(self):
        from paper_intensive_reading.formula_explainer import (
            build_empty_explanation, three_way_verify, FormulaSegment
        )

        expl = build_empty_explanation()
        expl.segments[5] = FormulaSegment(
            kind="code",
            content="```python\nimport numpy as np\nx = np.array([1,2,3])\nprint(x.sum())\n```",
        )

        result = three_way_verify(expl)
        assert "actual" in result
        assert result["actual"]["ok"]
        assert "6" in result["actual"]["stdout"]
