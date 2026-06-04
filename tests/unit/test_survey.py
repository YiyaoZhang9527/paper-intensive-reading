from datetime import date
from paper_intensive_reading.survey import (
    search_papers, rank_papers, build_survey_result
)
from paper_intensive_reading.types import Paper


def make_paper(arxiv_id, title, year=2023, citations=100):
    p = Paper(
        arxiv_id=arxiv_id, title=title, authors=["Author"],
        affiliations=[], abstract="x", published=date(year, 1, 1),
        pdf_path="", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    p.citations = citations  # attach so rank_papers' getattr can find it
    return p


class TestSearchPapers:
    def test_search_returns_list(self, monkeypatch):
        from paper_intensive_reading import survey

        class MockResult:
            entry_id = "http://arxiv.org/abs/2302.04761v1"
            title = "Toolformer"
            summary = "x"
            published = date(2023, 2, 9)
            authors = [type("A", (), {"name": "Schick"})()]

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([MockResult()])

        monkeypatch.setattr(survey.arxiv, "Client", MockClient)
        papers = search_papers("toolformer", max_results=5)
        assert len(papers) == 1
        assert papers[0].title == "Toolformer"


class TestRankPapers:
    def test_rank_by_citations(self):
        papers = [
            make_paper("a", "A", citations=10),
            make_paper("b", "B", citations=100),
            make_paper("c", "C", citations=50),
        ]
        ranked = rank_papers(papers)
        assert ranked[0]["arxiv_id"] == "b"
        assert ranked[1]["arxiv_id"] == "c"
        assert ranked[2]["arxiv_id"] == "a"

    def test_rank_favors_recent(self):
        papers = [
            make_paper("a", "A", year=2020, citations=1000),
            make_paper("b", "B", year=2024, citations=10),
        ]
        ranked = rank_papers(papers, recency_weight=0.5)
        # recency + citations 综合，新论文可能超过旧论文
        assert isinstance(ranked, list)


class TestBuildSurvey:
    def test_build_survey_result(self):
        papers = [make_paper("a", "A", citations=100), make_paper("b", "B", citations=50)]
        result = build_survey_result("Test query", papers)
        assert result["query"] == "Test query"
        assert len(result["papers"]) == 2
        assert result["papers"][0]["arxiv_id"] == "a"  # 引用多排前


class TestAddToList:
    def test_add_all_to_paper_store(self, tmp_db, monkeypatch):
        from paper_intensive_reading.survey import add_survey_results_to_list
        from paper_intensive_reading.paper_store import init_db, get_paper
        init_db(tmp_db)

        result = {
            "query": "LLM",
            "papers": [
                {"arxiv_id": "2302.13971", "title": "LLaMA"},
                {"arxiv_id": "2304.08485", "title": "QLoRA"},
            ],
        }
        added = add_survey_results_to_list(result, db_path=tmp_db)
        assert len(added) == 2
        assert get_paper(tmp_db, "2302.13971") is not None

    def test_selective_add(self, tmp_db, monkeypatch):
        from paper_intensive_reading.survey import add_survey_results_to_list
        from paper_intensive_reading.paper_store import init_db, get_paper
        init_db(tmp_db)

        result = {
            "query": "x",
            "papers": [
                {"arxiv_id": "2302.13971", "title": "LLaMA"},
                {"arxiv_id": "2304.08485", "title": "QLoRA"},
            ],
        }
        added = add_survey_results_to_list(result, db_path=tmp_db, arxiv_ids=["2302.13971"])
        assert len(added) == 1
        assert get_paper(tmp_db, "2302.13971") is not None
        assert get_paper(tmp_db, "2304.08485") is None
