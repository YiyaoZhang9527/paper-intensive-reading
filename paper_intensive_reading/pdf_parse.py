"""PDF 解析：元数据、章节、公式、图表、表格、算法。"""
import re
from pathlib import Path
from datetime import date

import fitz  # PyMuPDF
import pikepdf

from .errors import ParseError
from .types import Paper, Section, Paragraph, Formula, Figure, Table, Algorithm, Reference


DANGEROUS_KEYS = {"/JS", "/JavaScript", "/AA", "/OpenAction", "/Launch", "/URI", "/SubmitForm"}


def _scan_raw_bytes_for_dangerous(pdf_path: Path) -> str | None:
    """Fallback: scan raw bytes for dangerous keys. Returns first key found, or None."""
    try:
        data = pdf_path.read_bytes()
    except Exception:
        return None
    for key in DANGEROUS_KEYS:
        if key.encode("latin-1") in data:
            return key
    return None


def check_pdf_safety(pdf_path: Path) -> None:
    """检查 PDF 是否安全。危险时抛 ParseError。"""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise ParseError("default", path=str(pdf_path), detail="文件不存在")
    try:
        with pikepdf.open(pdf_path) as pdf:
            if pdf.is_encrypted:
                raise ParseError("encrypted", path=str(pdf_path))
            for obj in pdf.objects:
                obj_str = str(obj)
                for key in DANGEROUS_KEYS:
                    if key in obj_str:
                        raise ParseError("dangerous", path=str(pdf_path), detail=f"发现 {key}")
    except pikepdf.PasswordError as e:
        raise ParseError("encrypted", path=str(pdf_path)) from e
    except ParseError:
        raise
    except Exception as e:
        # Fallback: pikepdf failed to open. Still scan raw bytes for dangerous markers.
        found = _scan_raw_bytes_for_dangerous(pdf_path)
        if found:
            raise ParseError("dangerous", path=str(pdf_path), detail=f"发现 {found}") from e
        raise ParseError("default", path=str(pdf_path), detail=str(e)) from e


def extract_metadata(pdf_path: Path) -> dict:
    """提取 PDF 元数据。"""
    pdf_path = Path(pdf_path)
    metadata: dict = {
        "title": "", "authors": [], "abstract": "", "published": date.today(),
    }
    with fitz.open(pdf_path) as doc:
        info = doc.metadata or {}
        metadata["title"] = (info.get("title") or "").strip()
        metadata["authors"] = [a.strip() for a in (info.get("author") or "").split(",") if a.strip()]
        if not metadata["title"] and doc.page_count > 0:
            first_text = doc[0].get_text()
            lines = [l.strip() for l in first_text.split("\n") if l.strip()]
            if lines:
                metadata["title"] = lines[0][:200]
    return metadata


SECTION_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z][A-Za-z0-9 \-:_&/]{1,80})$",
    re.MULTILINE,
)


def _looks_like_section_title(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or len(line) > 100:
        return None
    m = SECTION_PATTERN.match(line)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def extract_sections(pdf_path: Path) -> list[Section]:
    """从 PDF 提取章节结构。"""
    pdf_path = Path(pdf_path)
    sections: list[Section] = []
    current: Section | None = None
    body_lines: list[str] = []

    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for line in text.split("\n"):
                parsed = _looks_like_section_title(line)
                if parsed is not None:
                    if current is not None:
                        current.paragraphs.append(
                            Paragraph(text="\n".join(body_lines).strip(), page=page_idx)
                        )
                        sections.append(current)
                    number, title = parsed
                    level = number.count(".") + 1
                    current = Section(number=number, title=title, level=level)
                    body_lines = []
                else:
                    if current is not None:
                        body_lines.append(line)

        if current is not None:
            current.paragraphs.append(
                Paragraph(text="\n".join(body_lines).strip(), page=doc.page_count - 1)
            )
            sections.append(current)

    if not sections:
        raise ParseError("no_sections", path=str(pdf_path))
    return sections


FORMULA_NUM_PATTERN = re.compile(
    r"\(?\b(?:Eq\.?|equation|formula|式)\s*\(?(\d+(?:\.\d+)?)\)?",
    re.IGNORECASE,
)
FIGURE_PATTERN = re.compile(
    r"Figure\s+(\d+)\s*[:.]\s*(.+?)(?=\n\s*(?:Figure|Table|\d+\.|\Z))",
    re.DOTALL,
)
TABLE_PATTERN = re.compile(
    r"Table\s+(\d+)\s*[:.]\s*(.+?)(?=\n\s*(?:Figure|Table|\d+\.|\Z))",
    re.DOTALL,
)
ALGORITHM_PATTERN = re.compile(r"Algorithm\s+(\d+)\s*[:.]\s*([^\n]+)")


def extract_formulas(pdf_path: Path) -> list[Formula]:
    """从 PDF 文本中提取公式编号（不 OCR 公式本身）。"""
    pdf_path = Path(pdf_path)
    formulas: list[Formula] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in FORMULA_NUM_PATTERN.finditer(text):
                number = f"({m.group(1)})"
                formulas.append(Formula(
                    number=number, latex="",
                    context_before=text[max(0, m.start() - 200):m.start()].strip(),
                    context_after=text[m.end():min(len(text), m.end() + 200)].strip(),
                    symbols={},
                ))
    # 去重
    seen: set[str] = set()
    unique = []
    for f in formulas:
        if f.number not in seen:
            seen.add(f.number)
            unique.append(f)
    return unique


def extract_figure_captions(pdf_path: Path) -> list[dict]:
    pdf_path = Path(pdf_path)
    captions: list[dict] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in FIGURE_PATTERN.finditer(text):
                captions.append({
                    "number": f"Figure {m.group(1)}",
                    "caption": m.group(2).strip()[:500],
                    "page": page_idx,
                })
    return captions


def extract_tables(pdf_path: Path) -> list[Table]:
    pdf_path = Path(pdf_path)
    tables: list[Table] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in TABLE_PATTERN.finditer(text):
                tables.append(Table(
                    number=f"Table {m.group(1)}",
                    caption=m.group(2).strip()[:500],
                    headers=[], rows=[],
                ))
    return tables


def extract_algorithms(pdf_path: Path) -> list[Algorithm]:
    pdf_path = Path(pdf_path)
    algos: list[Algorithm] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in ALGORITHM_PATTERN.finditer(text):
                title = m.group(2).strip()
                start = m.end()
                lines = text[start:].split("\n")[:20]
                pseudocode = "\n".join(lines).strip()
                algos.append(Algorithm(
                    number=f"Algorithm {m.group(1)}",
                    title=title, pseudocode=pseudocode,
                    language_hint="pseudocode",
                ))
    return algos
