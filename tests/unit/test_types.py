from datetime import date
from paper_intensive_reading.types import (
    Paper, Formula, Figure
)


def test_paper_creation():
    paper = Paper(
        arxiv_id="2302.13971",
        title="LLaMA: Open and Efficient Foundation Language Models",
        authors=["Touvron", "Lavril"],
        affiliations=["Meta AI"],
        abstract="We introduce LLaMA.",
        published=date(2023, 2, 27),
        pdf_path="/tmp/2302.13971.pdf",
        sections=[], figures=[], tables=[], algorithms=[], references=[],
    )
    assert paper.arxiv_id == "2302.13971"


def test_paper_to_dict():
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    d = paper.to_dict()
    assert d["arxiv_id"] == "2302.13971"
    assert d["published"] == "2023-02-27"


def test_paper_from_dict_roundtrip():
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    d = paper.to_dict()
    paper2 = Paper.from_dict(d)
    assert paper2.arxiv_id == paper.arxiv_id
    assert paper2.title == paper.title


def test_formula_creation():
    f = Formula(
        number="(1)",
        latex=r"\text{RMSNorm}(x) = \frac{x}{\sqrt{\text{Mean}(x^2)}} \cdot \gamma",
        context_before="We use RMSNorm.", context_after="It stabilizes.",
        symbols={"x": "input", "gamma": "scale"},
    )
    assert f.number == "(1)"


def test_figure_creation():
    fig = Figure(number="Figure 1", caption="Overview", image_path="/tmp/fig-1.png", page=3)
    assert fig.page == 3
