from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any


@dataclass
class Paragraph:
    text: str
    page: int


@dataclass
class Formula:
    number: str
    latex: str
    context_before: str
    context_after: str
    symbols: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Section:
    number: str
    title: str
    level: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    formulas: list[Formula] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "level": self.level,
            "paragraphs": [{"text": p.text, "page": p.page} for p in self.paragraphs],
            "formulas": [f.to_dict() for f in self.formulas],
        }


@dataclass
class Figure:
    number: str
    caption: str
    image_path: str
    page: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Table:
    number: str
    caption: str
    headers: list[str]
    rows: list[list[str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Algorithm:
    number: str
    title: str
    pseudocode: str
    language_hint: str = "pseudocode"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Reference:
    raw: str
    arxiv_id: str | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    affiliations: list[str]
    abstract: str
    published: date
    pdf_path: str
    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    algorithms: list[Algorithm] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": list(self.authors),
            "affiliations": list(self.affiliations),
            "abstract": self.abstract,
            "published": self.published.isoformat(),
            "pdf_path": self.pdf_path,
            "sections": [s.to_dict() for s in self.sections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "algorithms": [a.to_dict() for a in self.algorithms],
            "references": [r.to_dict() for r in self.references],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Paper":
        return cls(
            arxiv_id=d["arxiv_id"],
            title=d["title"],
            authors=d["authors"],
            affiliations=d["affiliations"],
            abstract=d["abstract"],
            published=date.fromisoformat(d["published"]),
            pdf_path=d["pdf_path"],
            sections=[
                Section(
                    number=s["number"], title=s["title"], level=s["level"],
                    paragraphs=[Paragraph(**p) for p in s["paragraphs"]],
                    formulas=[Formula(**f) for f in s["formulas"]],
                ) for s in d.get("sections", [])
            ],
            figures=[Figure(**f) for f in d.get("figures", [])],
            tables=[Table(**t) for t in d.get("tables", [])],
            algorithms=[Algorithm(**a) for a in d.get("algorithms", [])],
            references=[Reference(**r) for r in d.get("references", [])],
        )
