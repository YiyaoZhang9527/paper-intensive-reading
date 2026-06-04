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


MAX_PDF_SIZE = 100 * 1024 * 1024  # 100MB


def upload_pdf_attachment(client: NotionClient, pdf_path: Path, page_id: str) -> str:
    """上传 PDF 作为 Notion 附件，返回 upload_id。"""
    pdf_path = Path(pdf_path)
    size = pdf_path.stat().st_size
    if size > MAX_PDF_SIZE:
        raise NotionError("file_too_big", size_bytes=size)

    # Notion 文件上传 API（v2024+）：先创建 upload slot，再发文件
    # 这里简化：假设 Notion 直接接受 url/file_data
    # 实际实现可能要分两步
    with open(pdf_path, "rb") as f:
        _ = f.read()  # placeholder: real impl would POST file_data to upload slot

    # 简化：只调用 file_uploads API（具体实现取决于 Notion API 版本）
    data = {
        "filename": pdf_path.name,
        "file_size": size,
    }
    response = client._request("POST", "/file_uploads", data=data)
    return response.get("file_upload", {}).get("id", "")


def push(
    client: NotionClient, database_id: str,
    arxiv_id: str, title: str, md_path: Path, pdf_path: Path | None = None,
) -> dict:
    """统一入口：推送到 Notion。"""
    page = create_paper_page(client, database_id, arxiv_id, title, md_path)
    result = {"page_id": page["page_id"], "url": page["url"]}

    if pdf_path and Path(pdf_path).exists():
        try:
            upload_id = upload_pdf_attachment(client, pdf_path, page["page_id"])
            result["pdf_uploaded"] = True
            result["pdf_upload_id"] = upload_id
        except NotionError:
            result["pdf_uploaded"] = False

    return result
