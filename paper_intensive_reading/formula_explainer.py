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
