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
