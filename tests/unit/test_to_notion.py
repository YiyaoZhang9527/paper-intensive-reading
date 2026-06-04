import pytest
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


class TestCreatePage:
    def test_create_page_with_content(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, create_paper_page

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-123")

        md_file = tmp_path / "note.md"
        md_file.write_text("# LLaMA\n\nTest content")

        # Mock 客户端
        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                if method == "POST" and "/pages" in path:
                    return {"id": "page-abc123", "url": "https://notion.so/page-abc123"}
                return {}

        client = MockClient("test_key")
        result = create_paper_page(
            client=client,
            database_id="db-123",
            arxiv_id="2302.13971",
            title="LLaMA",
            md_path=md_file,
        )

        assert result["page_id"] == "page-abc123"
        assert "notion.so" in result["url"]

    def test_page_creation_error(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, create_paper_page
        from paper_intensive_reading.errors import NotionError

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        md_file = tmp_path / "note.md"
        md_file.write_text("x")

        class FailingClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                raise NotionError("default", detail="server down")

        client = FailingClient("test_key")
        with pytest.raises(NotionError):
            create_paper_page(client, "db-123", "2302.13971", "LLaMA", md_file)


class TestPdfUpload:
    def test_upload_pdf_under_size(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, upload_pdf_attachment

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%small\n")

        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                return {"file_upload": {"id": "upload-123"}}

        client = MockClient("test_key")
        result = upload_pdf_attachment(client, pdf, "page-abc")
        assert result == "upload-123"

    def test_upload_pdf_too_big(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, upload_pdf_attachment
        from paper_intensive_reading.errors import NotionError

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        pdf = tmp_path / "huge.pdf"
        # 写一个 > 100MB 的文件
        with open(pdf, "wb") as f:
            f.write(b"x" * (101 * 1024 * 1024))

        client = NotionClient("test_key")
        with pytest.raises(NotionError) as exc:
            upload_pdf_attachment(client, pdf, "page-abc")
        assert exc.value.subtype == "file_too_big"


class TestPush:
    def test_push_to_notion(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, push

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-123")

        md = tmp_path / "note.md"
        md.write_text("# LLaMA\n\nTest")
        pdf = tmp_path / "2302.13971.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%fake\n")

        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                if "/pages" in path:
                    return {"id": "page-abc", "url": "https://notion.so/page-abc"}
                if "file_uploads" in path:
                    return {"file_upload": {"id": "upload-xyz"}}
                return {}

        client = MockClient("test_key")
        result = push(
            client=client, database_id="db-123",
            arxiv_id="2302.13971", title="LLaMA",
            md_path=md, pdf_path=pdf,
        )
        assert result["page_id"] == "page-abc"
        assert result["pdf_uploaded"] is True
