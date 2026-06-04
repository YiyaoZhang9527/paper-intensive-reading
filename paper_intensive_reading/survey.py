"""领域调研：从 arXiv 拉论文列表并按引用 + 时效排序。"""
import arxiv
from datetime import date
from .types import Paper


def search_papers(query: str, max_results: int = 20, months: int = 6) -> list[Paper]:
    """从 arXiv 搜索论文。"""
    search = arxiv.Search(
        query=query, max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    client = arxiv.Client(page_size=max_results, delay_seconds=3.0, num_retries=3)
    results = list(client.results(search))

    papers = []
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


def rank_papers(papers: list[Paper], recency_weight: float = 0.3) -> list[dict]:
    """按引用 + 时效综合排序。返回 [{arxiv_id, title, score, ...}]。"""
    # 简化：没有真实 citation 数据，假设 citations=100 的 paper 有 100 引用
    # 实际：需要从 Semantic Scholar API 拉
    today_year = date.today().year
    scored = []
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


def build_survey_result(query: str, papers: list[Paper]) -> dict:
    """构造调研结果。"""
    ranked = rank_papers(papers)
    return {
        "query": query,
        "paper_count": len(papers),
        "papers": ranked,
        "generated_at": date.today().isoformat(),
    }
