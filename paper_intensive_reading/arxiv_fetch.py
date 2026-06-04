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
