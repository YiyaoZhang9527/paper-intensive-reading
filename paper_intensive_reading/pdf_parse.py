"""PDF 解析：元数据、章节、公式、图表、表格、算法。"""
import re
from pathlib import Path
from datetime import date

import fitz  # PyMuPDF
import pikepdf

from .errors import ParseError
from .types import Paper, Section, Paragraph, Formula, Figure, Table, Algorithm


DANGEROUS_KEYS = {"/JS", "/JavaScript", "/Launch", "/SubmitForm"}


def _has_dangerous_combo(pdf) -> bool:
    """检查 /AA / /OpenAction / /URI 是否与 /Launch 组合出现（才危险）。"""
    try:
        for obj in pdf.objects:
            obj_str = str(obj)
            # /Launch + 任何 URI 链接 = 真正危险
            if "/Launch" in obj_str:
                return True
            # /SubmitForm + /URI = 数据外泄
            if "/SubmitForm" in obj_str and "/URI" in obj_str:
                return True
    except Exception:
        return False
    return False


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
            # 先检查对象层（结构化检查）
            for obj in pdf.objects:
                obj_str = str(obj)
                for key in DANGEROUS_KEYS:
                    if key in obj_str:
                        raise ParseError("dangerous", path=str(pdf_path), detail=f"发现 {key}")
            # 再检查危险组合（OpenAction/URI 单独无害，组合才危险）
            if _has_dangerous_combo(pdf):
                raise ParseError("dangerous", path=str(pdf_path), detail="发现危险组合（/Launch + /URI 或 /SubmitForm + /URI）")
    except pikepdf.PasswordError as e:
        raise ParseError("encrypted", path=str(pdf_path)) from e
    except ParseError:
        raise
    except Exception as e:
        # 解析失败（malformed PDF）走降级：扫描原始字节
        if _scan_raw_bytes_for_dangerous(pdf_path):
            raise ParseError("dangerous", path=str(pdf_path), detail="原始字节扫描发现危险标记")
        raise ParseError("default", path=str(pdf_path), detail=str(e)) from e


def _scan_raw_bytes_for_dangerous(pdf_path: Path) -> bool:
    """malformed PDF 兜底：扫描原始字节。仅检测真正危险的（/JS, /Launch + URL）。"""
    try:
        data = pdf_path.read_bytes()
    except Exception:
        return False
    # 只对真正危险的模式报警；/OpenAction 和 /URI 单独无害
    if b"/JavaScript" in data or b"/JS " in data or b"/JS\n" in data:
        return True
    return False


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
            lines = [ln.strip() for ln in first_text.split("\n") if ln.strip()]
            if lines:
                metadata["title"] = lines[0][:200]
    return metadata


SECTION_PATTERN_SAME_LINE = re.compile(
    r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z][A-Za-z0-9 \-:_&/()]{1,80})$"
)
SECTION_NUMBER_ONLY = re.compile(r"^(\d+(?:\.\d+)*)$")


def _looks_like_section_title(lines: list[str], idx: int) -> tuple[str, str] | None:
    """检查 lines[idx] 是否是章节标题（支持同行或下一行）。"""
    if idx >= len(lines):
        return None
    line = lines[idx].strip()
    if not line or len(line) > 100:
        return None
    # 情况 1: 同行 "2 Related work"
    m = SECTION_PATTERN_SAME_LINE.match(line)
    if m:
        number = m.group(1)
        if _is_real_section_number(number):
            return number, m.group(2).strip()
    # 情况 2: 数字独占一行，下一行是标题
    m = SECTION_NUMBER_ONLY.match(line)
    if m and idx + 1 < len(lines):
        number = m.group(1)
        next_line = lines[idx + 1].strip()
        if (_is_real_section_number(number) and next_line
                and len(next_line) < 100 and next_line[0].isupper()
                and not next_line[0].isdigit()):
            return number, next_line
    return None


def _is_real_section_number(number: str) -> bool:
    """判断一个数字串是否像真实章节号。规则：主部分 <= 9，子部分都 <= 9。"""
    parts = number.split(".")
    try:
        # 顶级部分必须 1-9 (排除 82.47 这种表格数据)
        if int(parts[0]) > 9 or int(parts[0]) < 1:
            return False
        # 子部分都 <= 9
        for p in parts[1:]:
            if int(p) > 9:
                return False
    except (ValueError, IndexError):
        return False
    return True


def extract_sections(pdf_path: Path) -> list[Section]:
    """从 PDF 提取章节结构。"""
    pdf_path = Path(pdf_path)
    sections: list[Section] = []
    current: Section | None = None
    body_lines: list[str] = []

    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            lines = text.split("\n")
            i = 0
            while i < len(lines):
                parsed = _looks_like_section_title(lines, i)
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
                    # 跳过标题行（如果数字和标题在不同行）
                    if SECTION_NUMBER_ONLY.match(lines[i].strip()) and i + 1 < len(lines):
                        i += 2
                    else:
                        i += 1
                else:
                    if current is not None and lines[i].strip():
                        body_lines.append(lines[i].strip())
                    i += 1

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


def parse(pdf_path: str | Path) -> Paper:
    """解析 PDF 为 Paper 对象。统一入口。"""
    pdf_path = Path(pdf_path)

    check_pdf_safety(pdf_path)
    meta = extract_metadata(pdf_path)
    sections = extract_sections(pdf_path)
    formulas = extract_formulas(pdf_path)
    figures_meta = extract_figure_captions(pdf_path)
    tables = extract_tables(pdf_path)
    algorithms = extract_algorithms(pdf_path)

    # 公式归入对应章节
    for f in formulas:
        for sec in sections:
            if any(f.number in p.text for p in sec.paragraphs):
                sec.formulas.append(f)
                break

    # Figure 对象
    figures = [
        Figure(
            number=fig["number"], caption=fig["caption"],
            image_path="", page=fig["page"],
        )
        for fig in figures_meta
    ]

    abstract = meta.get("abstract", "")
    if not abstract and sections:
        for sec in sections:
            if "abstract" in sec.title.lower():
                abstract = "\n".join(p.text for p in sec.paragraphs)
                break

    return Paper(
        arxiv_id="",
        title=meta.get("title", ""),
        authors=meta.get("authors", []),
        affiliations=meta.get("affiliations", []),
        abstract=abstract,
        published=meta.get("published") or date.today(),
        pdf_path=str(pdf_path),
        sections=sections, figures=figures, tables=tables,
        algorithms=algorithms, references=[],
    )
