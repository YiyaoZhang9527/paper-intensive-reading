"""公式讲解 6 段引擎：原始 → 白话 → 符号 → 类比 → 计算示例 → NumPy 代码。"""
from dataclasses import dataclass, field
from typing import Any

from .types import Formula


SEGMENT_KINDS = ["original", "plain", "symbols", "analogy", "example", "code"]


@dataclass
class FormulaSegment:
    kind: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "content": self.content, **self.meta}


@dataclass
class FormulaExplanation:
    arxiv_id: str
    formula_number: str
    latex: str
    segments: list[FormulaSegment]
    verified: bool = False
    verification_outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "formula_number": self.formula_number,
            "latex": self.latex,
            "segments": [s.to_dict() for s in self.segments],
            "verified": self.verified,
            "verification_outputs": self.verification_outputs,
        }


@dataclass
class ExplanationContext:
    arxiv_id: str
    depth_pref: str = "elementary"  # "elementary" | "medium" | "deep"
    ladder_layers: list[int] = field(default_factory=list)
    user_feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "depth_pref": self.depth_pref,
            "ladder_layers": self.ladder_layers,
            "user_feedback": self.user_feedback,
        }


def build_empty_explanation() -> FormulaExplanation:
    return FormulaExplanation(
        arxiv_id="",
        formula_number="",
        latex="",
        segments=[FormulaSegment(kind=k, content="") for k in SEGMENT_KINDS],
    )


FORMULA_PROMPT_TEMPLATE = """你是 AI 论文公式讲解助手。用户数学基础: {depth_pref}。
你需要为一个公式生成 6 段讲解。

## 段 1：原始形式（LaTeX）
输出公式的 LaTeX 源码。

## 段 2：白话翻译
用一句中文（不超过 30 字）解释公式在算什么。

## 段 3：逐符号解释
列出公式里每个符号，标注它属于数学概念阶梯的哪一层（如 "第 5 层：向量"）。

## 段 4：直觉类比
用生活场景（图书馆、开车、做饭、购物等）解释公式的核心思想。

## 段 5：详细计算示例
用 d=2 或 d=4 的极小例子，手算可验证。

## 段 6：NumPy 代码实现
用 NumPy 写代码实现这个公式（必须只用 import numpy）。代码要可独立运行。

待讲解公式:
- 编号: {formula_number}
- LaTeX: {latex}
- 上下文（前 200 字）: {context_before}
- 上下文（后 200 字）: {context_after}

请按 6 段输出，每段用 "## 段 N" 开头。
"""
import re


def call_llm(prompt: str, **kwargs) -> str:
    """调用 LLM 的占位函数。实际实现由调用方注入（便于测试）。"""
    raise NotImplementedError("call_llm must be injected by caller")


def parse_llm_response(response: str) -> list[FormulaSegment]:
    """解析 LLM 返回的 6 段输出。"""
    # 用 "## 段 N" 切分
    pattern = re.compile(r"##\s*段\s*(\d+)\s*\n", re.MULTILINE)
    matches = list(pattern.finditer(response))
    if len(matches) < 6:
        # 失败：返回空段
        return [FormulaSegment(kind=k, content="") for k in SEGMENT_KINDS]

    segments = []
    for i in range(6):
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(response)
        content = response[start:end].strip()
        segments.append(FormulaSegment(kind=SEGMENT_KINDS[i], content=content))
    return segments


def explain_formula(
    formula: Formula,
    arxiv_id: str,
    llm_fn=None,
) -> FormulaExplanation:
    """调用 LLM 生成 6 段讲解。"""
    from .errors import LLMError

    if llm_fn is None:
        llm_fn = call_llm

    prompt = FORMULA_PROMPT_TEMPLATE.format(
        depth_pref="elementary",
        formula_number=formula.number,
        latex=formula.latex,
        context_before=formula.context_before[:200],
        context_after=formula.context_after[:200],
    )

    try:
        response = llm_fn(prompt)
    except Exception as e:
        raise LLMError("default", detail=str(e)) from e

    if not response or len(response) < 50:
        raise LLMError("bad_format", detail="LLM 返回过短")

    segments = parse_llm_response(response)
    if not any(s.content for s in segments):
        raise LLMError("bad_format", detail="无法解析任何段")

    return FormulaExplanation(
        arxiv_id=arxiv_id,
        formula_number=formula.number,
        latex=formula.latex,
        segments=segments,
    )


from .numpy_runner import run as run_numpy


def extract_code(segment_content: str) -> str:
    """从段[6]的 markdown 文本里提取 ```python ... ``` 代码块。"""
    pattern = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
    m = pattern.search(segment_content)
    if m:
        return m.group(1).strip()
    # fallback: 整段当作代码
    return segment_content.strip()


def verify_code_segment(code: str, **run_kwargs) -> dict:
    """调用 numpy_runner 跑代码，返回结构化结果。"""
    result = run_numpy(code, **run_kwargs)
    return result.to_dict()


def three_way_verify(
    explanation: FormulaExplanation,
) -> dict:
    """三对照：手算（段[5]）vs 代码（段[6]）vs 实际跑出。"""
    if len(explanation.segments) < 6:
        return {"hand": "", "code": "", "actual": {"ok": False, "stdout": ""}}

    hand = explanation.segments[4].content  # 段[5] 手算
    code_segment = explanation.segments[5].content
    code = extract_code(code_segment)
    actual = verify_code_segment(code)

    return {
        "hand": hand,
        "code": code,
        "actual": actual,
    }
