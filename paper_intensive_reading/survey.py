"""领域调研：从 arXiv 拉论文列表并按引用 + 时效排序。"""
import time
from datetime import date
from pathlib import Path
from typing import Any

import arxiv

from .errors import FetchError
from .types import Paper


def search_papers(query: str, max_results: int = 20, months: int = 6) -> list[Paper]:
    """从 arXiv 搜索论文。"""
    import arxiv as arxiv_mod

    search = arxiv.Search(
        query=query, max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    # 手动处理 429 限流（arxiv 库的默认 num_retries 偶尔不够）
    last_err = None
    for attempt in range(5):
        try:
            client = arxiv.Client(
                page_size=max_results,
                delay_seconds=3.0 + attempt * 2,  # 3s, 5s, 7s, 9s, 11s
                num_retries=3,
            )
            results = list(client.results(search))
            break
        except arxiv_mod.HTTPError as e:
            last_err = e
            if getattr(e, "status", None) == 429 and attempt < 4:
                wait = 15 * (attempt + 1)  # 15s, 30s, 45s, 60s
                time.sleep(wait)
                continue
            raise FetchError("arxiv_timeout", query=query, detail=str(e)) from e
        except Exception as e:
            raise FetchError("arxiv_timeout", query=query, detail=str(e)) from e
    else:
        raise FetchError("arxiv_timeout", query=query, detail=f"重试 5 次仍 429: {last_err}")

    papers: list[Paper] = []
    for r in results:
        arxiv_id = r.entry_id.split("/")[-1]
        arxiv_id = arxiv_id.lower().rstrip("v0123456789") or arxiv_id
        pub = r.published
        if pub is None:
            pub_date = date.today()
        elif hasattr(pub, "date") and callable(pub.date):
            pub_date = pub.date()
        else:
            pub_date = pub  # already a date
        papers.append(Paper(
            arxiv_id=arxiv_id, title=r.title,
            authors=[a.name for a in r.authors], affiliations=[],
            abstract=r.summary,
            published=pub_date,
            pdf_path="", sections=[], figures=[], tables=[],
            algorithms=[], references=[],
        ))
    return papers


def rank_papers(papers: list[Paper], recency_weight: float = 0.3) -> list[dict[str, Any]]:
    """按引用 + 时效综合排序。返回 [{arxiv_id, title, score, ...}]。"""
    # 简化：没有真实 citation 数据，假设 citations=100 的 paper 有 100 引用
    # 实际：需要从 Semantic Scholar API 拉
    today_year = date.today().year
    scored: list[dict[str, Any]] = []
    for p in papers:
        # 时效分：年差越小越高
        recency = max(0, 1 - (today_year - p.published.year) * 0.2)
        # 引用分：citations / max_citations（归一化）
        citations = getattr(p, "citations", 100)  # 缺省
        # score 简化计算
        score = citations * (1 - recency_weight) + recency * 1000 * recency_weight
        scored.append({
            "arxiv_id": p.arxiv_id, "title": p.title,
            "authors": p.authors, "year": p.published.year,
            "abstract": p.abstract[:200],
            "citations": citations, "score": score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def build_survey_result(query: str, papers: list[Paper]) -> dict[str, Any]:
    """构造调研结果。"""
    ranked = rank_papers(papers)
    return {
        "query": query,
        "paper_count": len(papers),
        "papers": ranked,
        "generated_at": date.today().isoformat(),
    }


def add_survey_results_to_list(
    result: dict[str, Any], db_path: str | Path, arxiv_ids: list[str] | None = None,
) -> list[str]:
    """把调研结果里的论文添加到阅读清单。arxiv_ids=None 表示全部添加。"""
    from .paper_store import add_paper
    added: list[str] = []
    for p in result.get("papers", []):
        if arxiv_ids and p["arxiv_id"] not in arxiv_ids:
            continue
        add_paper(db_path, {
            "arxiv_id": p["arxiv_id"], "title": p["title"],
            "authors": p.get("authors", []), "affiliations": [],
            "abstract": p.get("abstract", ""), "published": date(p.get("year", 2024), 1, 1),
            "pdf_path": "",
        })
        added.append(p["arxiv_id"])
    return added
