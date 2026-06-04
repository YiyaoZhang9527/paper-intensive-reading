"""从多个来源获取论文 PDF。"""
import re
from pathlib import Path
from datetime import date

import arxiv
import requests

from .errors import FetchError
from .types import Paper

ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
ARXIV_URL_PATTERN = re.compile(
    r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?"
)


def validate_arxiv_id(arxiv_id: str) -> bool:
    """验证 arXiv ID 格式。失败抛 FetchError(arxiv_404)。"""
    if not arxiv_id or not ARXIV_ID_PATTERN.match(arxiv_id):
        raise FetchError("arxiv_404", arxiv_id=arxiv_id)
    return True


def normalize_arxiv_id(arxiv_id: str) -> str:
    """去掉版本号，统一为小写。"""
    s = arxiv_id.lower()
    # 去掉 v + 数字后缀
    if "v" in s:
        base, _, ver = s.rpartition("v")
        if ver.isdigit():
            return base
    return s


def extract_id_from_url(url: str) -> str:
    """从 arXiv URL 提取 ID（保留版本号）。"""
    m = ARXIV_URL_PATTERN.search(url)
    if not m:
        raise FetchError("arxiv_404", url=url)
    return m.group(1)


def _is_valid_pdf(p: Path) -> bool:
    try:
        with open(p, "rb") as f:
            return f.read(5).startswith(b"%PDF-")
    except OSError:
        return False


def fetch_by_arxiv_id(arxiv_id: str, dest: Path) -> Path:
    """根据 arXiv ID 下载 PDF。返回本地路径。"""
    validate_arxiv_id(arxiv_id)
    normalized = normalize_arxiv_id(arxiv_id)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    target = dest / f"{normalized}.pdf"
    if target.exists() and _is_valid_pdf(target):
        return target  # 已存在，跳过

    try:
        search = arxiv.Search(id_list=[arxiv_id])
        client = arxiv.Client(page_size=1, delay_seconds=3.0, num_retries=3)
        result = next(client.results(search))
        result.download_pdf(dirpath=str(dest), filename=f"{normalized}.pdf")
    except arxiv.UnexpectedEmptyPageError as e:
        raise FetchError("arxiv_404", arxiv_id=arxiv_id) from e
    except StopIteration as e:
        raise FetchError("arxiv_404", arxiv_id=arxiv_id) from e
    except arxiv.HTTPError as e:
        if getattr(e, "status", None) == 503:
            raise FetchError("arxiv_503", arxiv_id=arxiv_id) from e
        raise FetchError("arxiv_timeout", arxiv_id=arxiv_id) from e
    except Exception as e:
        raise FetchError("default", arxiv_id=arxiv_id, detail=str(e)) from e

    if not target.exists() or not _is_valid_pdf(target):
        raise FetchError("invalid_pdf", arxiv_id=arxiv_id)

    return target
