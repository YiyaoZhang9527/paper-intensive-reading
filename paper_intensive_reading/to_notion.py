"""同步到 Notion 数据库。"""
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from .errors import NotionError


NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def get_api_key() -> str:
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        raise NotionError("no_api_key")
    return key


def get_database_id() -> str:
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if not db_id:
        raise NotionError("no_db")
    return db_id


class NotionClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key()
        self.base_url = BASE_URL

    def _request(self, method: str, path: str, data: dict | None = None, max_retries: int = 3) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:  # rate limit
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise NotionError("rate_limit") from e
                raise NotionError("default", detail=f"HTTP {e.code}: {e.reason}") from e
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise NotionError("default", detail=str(e)) from e
        return {}


def _md_to_blocks(md_text: str) -> list[dict]:
    """简单把 Markdown 转为 Notion blocks。"""
    blocks = []
    for line in md_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}
            })
        elif line.startswith("> "):
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        elif line.startswith("```"):
            blocks.append({
                "object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": "[code block]"}}],
                         "language": "python"}
            })
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]}
            })
    return blocks[:100]  # Notion 限制：单次最多 100 块


def create_paper_page(
    client: NotionClient, database_id: str,
    arxiv_id: str, title: str, md_path: Path,
) -> dict:
    """在 Notion 数据库里创建论文 page。"""
    md_path = Path(md_path)
    md_text = md_path.read_text()
    blocks = _md_to_blocks(md_text)

    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Arxiv ID": {"rich_text": [{"text": {"content": arxiv_id}}]},
        },
        "children": blocks,
    }
    response = client._request("POST", "/pages", data=data)
    return {"page_id": response.get("id", ""), "url": response.get("url", "")}
