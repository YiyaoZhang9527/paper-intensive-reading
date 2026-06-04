import pytest
from datetime import date
from paper_intensive_reading.compare import (
    compare_papers, build_aspect_table, DEFAULT_ASPECTS
)
from paper_intensive_reading.types import Paper


def make_paper(arxiv_id, title, year=2023):
    return Paper(
        arxiv_id=arxiv_id, title=title, authors=["X"],
        affiliations=[], abstract="x", published=date(year, 1, 1),
        pdf_path=f"/tmp/{arxiv_id}.pdf",
        sections=[], figures=[], tables=[], algorithms=[], references=[],
    )


class TestCompare:
    def test_default_aspects_exist(self):
        assert "time" in DEFAULT_ASPECTS
        assert "model_size" in DEFAULT_ASPECTS

    def test_compare_two_papers(self):
        papers = [make_paper("a", "A"), make_paper("b", "B")]
        result = compare_papers(papers)
        assert result["paper_count"] == 2
        assert "aspects" in result
        assert "A" in str(result["aspects"])

    def test_compare_empty(self):
        with pytest.raises(ValueError):
            compare_papers([])

    def test_aspect_table_2d(self):
        papers = [make_paper("a", "A"), make_paper("b", "B")]
        table = build_aspect_table(papers)
        assert isinstance(table, dict)
        assert "time" in table
        # time 应该是 [a_year, b_year]
        assert table["time"] == [2023, 2023]


class TestAspectExtraction:
    def test_extract_authors(self):
        paper = make_paper("a", "A")
        paper.authors = ["Touvron", "Lavril"]
        result = compare_papers([paper])
        assert result["aspects"]["authors"][0] == "Touvron, Lavril"


class TestMethodExtraction:
    def test_extract_keyword(self):
        from paper_intensive_reading.compare import extract_method_keywords
        abstract = "We propose a transformer-based model with RoPE positional encoding and RMSNorm."
        kws = extract_method_keywords(abstract)
        assert "transformer" in kws
        assert "RoPE" in kws or "rope" in [k.lower() for k in kws]

    def test_extract_datasets(self):
        from paper_intensive_reading.compare import extract_dataset_names
        abstract = "We evaluate on ImageNet, COCO, and GLUE benchmarks."
        datasets = extract_dataset_names(abstract)
        assert "ImageNet" in datasets
        assert "COCO" in datasets
