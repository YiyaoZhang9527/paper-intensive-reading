"""多论文并排对比。"""
from typing import Any

from .types import Paper


DEFAULT_ASPECTS = [
    "time", "authors", "model_size", "method", "datasets", "main_result"
]


def build_aspect_table(papers: list[Paper], aspects: list[str] | None = None) -> dict[str, list[Any]]:
    """构建 {aspect: [paper1_value, paper2_value, ...]}。"""
    aspects = aspects or DEFAULT_ASPECTS
    table: dict[str, list[Any]] = {"title": [p.title for p in papers]}
    for a in aspects:
        table[a] = []

    for p in papers:
        table["time"].append(p.published.year)
        table["authors"].append(", ".join(p.authors))
        table["model_size"].append("(待解析)")
        table["method"].append(p.abstract[:200])
        table["datasets"].append("(待解析)")
        table["main_result"].append("(待解析)")

    return table


def compare_papers(papers: list[Paper], aspects: list[str] | None = None) -> dict[str, Any]:
    """多论文对比的统一入口。"""
    if not papers:
        raise ValueError("至少需要 1 篇论文")
    aspects = aspects or DEFAULT_ASPECTS
    table = build_aspect_table(papers, aspects)
    return {
        "paper_count": len(papers),
        "paper_titles": [p.title for p in papers],
        "arxiv_ids": [p.arxiv_id for p in papers],
        "aspects": table,
    }


import re  # noqa: E402

METHOD_KEYWORDS = [
    "transformer", "attention", "self-attention", "cross-attention",
    "BERT", "GPT", "LLaMA", "RoPE", "RMSNorm", "LayerNorm", "SwiGLU",
    "LoRA", "RLHF", "fine-tuning", "pre-training", "distillation",
    "MoE", "sparse", "quantization", "pruning",
]

DATASET_KEYWORDS = [
    "ImageNet", "COCO", "GLUE", "SuperGLUE", "MMLU",
    "HumanEval", "GSM8K", "MATH", "HellaSwag", "ARC",
    "CommonsenseQA", "WinoGrande", "TruthfulQA",
    "SQuAD", "Natural Questions", "TriviaQA",
]


def extract_method_keywords(text: str) -> list[str]:
    found: list[str] = []
    for kw in METHOD_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
            found.append(kw)
    return found


def extract_dataset_names(text: str) -> list[str]:
    found: list[str] = []
    for ds in DATASET_KEYWORDS:
        if re.search(rf"\b{re.escape(ds)}\b", text, re.IGNORECASE):
            found.append(ds)
    return found
