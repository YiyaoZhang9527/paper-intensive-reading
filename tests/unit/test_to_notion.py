import os
import pytest
from pathlib import Path
from paper_intensive_reading.to_notion import (
    get_api_key, get_database_id, NotionClient
)
from paper_intensive_reading.errors import NotionError


class TestConfig:
    def test_get_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_test_123")
        assert get_api_key() == "secret_test_123"

    def test_get_api_key_missing_raises(self, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        with pytest.raises(NotionError) as exc:
            get_api_key()
        assert exc.value.subtype == "no_api_key"

    def test_get_database_id_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-12345")
        assert get_database_id() == "db-12345"

    def test_get_database_id_missing_raises(self, monkeypatch):
        monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
        with pytest.raises(NotionError) as exc:
            get_database_id()
        assert exc.value.subtype == "no_db"


class TestNotionClient:
    def test_client_initialization(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        client = NotionClient()
        assert client.api_key == "secret_xyz"
        assert client.base_url == "https://api.notion.com/v1"

    def test_client_missing_key(self, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        with pytest.raises(NotionError):
            NotionClient()
