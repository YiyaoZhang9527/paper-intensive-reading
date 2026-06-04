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
