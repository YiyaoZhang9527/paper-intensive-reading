import pytest
from pathlib import Path
from datetime import date
from paper_intensive_reading.arxiv_fetch import (
    validate_arxiv_id, normalize_arxiv_id, extract_id_from_url
)
from paper_intensive_reading.errors import FetchError


class TestValidateArxivId:
    def test_valid_id(self):
        assert validate_arxiv_id("2302.13971") is True

    def test_valid_id_with_version(self):
        assert validate_arxiv_id("2302.13971v1") is True
        assert validate_arxiv_id("2302.13971v3") is True

    def test_invalid_id_letters(self):
        with pytest.raises(FetchError) as exc:
            validate_arxiv_id("abc.def")
        assert exc.value.subtype == "arxiv_404"

    def test_invalid_id_too_short(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("2302.139")

    def test_invalid_id_too_long(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("2302.139711234")

    def test_empty_id(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("")


class TestNormalizeArxivId:
    def test_strip_version(self):
        assert normalize_arxiv_id("2302.13971v2") == "2302.13971"

    def test_no_version(self):
        assert normalize_arxiv_id("2302.13971") == "2302.13971"

    def test_uppercase(self):
        assert normalize_arxiv_id("2302.13971V2") == "2302.13971"


class TestExtractIdFromUrl:
    def test_abs_url(self):
        assert extract_id_from_url("https://arxiv.org/abs/2302.13971") == "2302.13971"

    def test_pdf_url(self):
        assert extract_id_from_url("https://arxiv.org/pdf/2302.13971") == "2302.13971"

    def test_pdf_url_with_version(self):
        assert extract_id_from_url("https://arxiv.org/pdf/2302.13971v2.pdf") == "2302.13971v2"

    def test_invalid_url(self):
        with pytest.raises(FetchError):
            extract_id_from_url("https://example.com/not-an-arxiv")


class TestDownloadPdf:
    def test_download_to_path(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        class MockResult:
            entry_id = "http://arxiv.org/abs/2302.13971v1"
            title = "Test Paper"
            pdf_url = "http://arxiv.org/pdf/2302.13971v1"
            authors = [type("A", (), {"name": "Test Author"})()]
            summary = "Test abstract."
            published = date(2023, 2, 27)

            def download_pdf(self, dirpath, filename):
                Path(dirpath).mkdir(parents=True, exist_ok=True)
                Path(dirpath, filename).write_bytes(b"%PDF-1.4\n%fake\n")
                return str(Path(dirpath) / filename)

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([MockResult()])

        monkeypatch.setattr(arxiv_fetch.arxiv, "Client", MockClient)

        pdf_path = arxiv_fetch.fetch_by_arxiv_id("2302.13971", dest=tmp_workspace)
        assert pdf_path.exists()
        assert pdf_path.name == "2302.13971.pdf"
        assert pdf_path.stat().st_size > 0

    def test_invalid_id_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_arxiv_id("bad-id", dest=tmp_workspace)

    def test_cached_pdf_not_redownloaded(self, tmp_workspace):
        """已存在的 PDF 不重新下载"""
        from paper_intensive_reading import arxiv_fetch
        cached = tmp_workspace / "2302.13971.pdf"
        cached.write_bytes(b"%PDF-1.4\n%already cached\n")

        # 即使 arxiv 调用失败，缓存也应被返回
        pdf_path = arxiv_fetch.fetch_by_arxiv_id("2302.13971", dest=tmp_workspace)
        assert pdf_path == cached


class TestFetchByUrl:
    def test_fetch_from_url(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target

        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        pdf_path = arxiv_fetch.fetch_by_url("https://arxiv.org/abs/2302.13971", dest=tmp_workspace)
        assert pdf_path.exists()
        assert pdf_path.name == "2302.13971.pdf"

    def test_non_arxiv_url_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_url("https://example.com/paper.pdf", dest=tmp_workspace)


class TestFetchByLocalPath:
    def test_valid_local_pdf(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        pdf = tmp_workspace / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%fake pdf content here\n")

        result = arxiv_fetch.fetch_by_local_path(str(pdf))
        assert result == pdf

    def test_nonexistent_path_raises(self):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError) as exc:
            arxiv_fetch.fetch_by_local_path("/tmp/does-not-exist.pdf")
        assert exc.value.subtype == "arxiv_404"

    def test_non_pdf_file_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        txt = tmp_workspace / "test.txt"
        txt.write_text("not a pdf")
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_local_path(str(txt))

    def test_magic_byte_validation(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        pdf = tmp_workspace / "fake.pdf"
        pdf.write_bytes(b"NOT A PDF AT ALL")
        with pytest.raises(FetchError) as exc:
            arxiv_fetch.fetch_by_local_path(str(pdf))
        assert exc.value.subtype == "invalid_pdf"


class TestFetchByBibtex:
    def test_parse_bibtex_with_eprint(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = """
@article{llama2023,
  title={LLaMA: Open and Efficient Foundation Language Models},
  author={Touvron and Lavril},
  year={2023},
  eprint={2302.13971},
  archivePrefix={arXiv}
}
"""
        arxiv_id = arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)
        assert arxiv_id == "2302.13971"

    def test_parse_bibtex_with_arxiv_url(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = """
@article{llama, title={LLaMA}, eprint={https://arxiv.org/abs/2302.13971}}
"""
        arxiv_id = arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)
        assert arxiv_id == "2302.13971"

    def test_parse_bibtex_no_id_raises(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = "@article{foo, title={No arxiv ID}}"
        with pytest.raises(FetchError):
            arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)

    def test_fetch_by_bibtex(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch
        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target
        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        bibtex = "@article{x, eprint={2302.13971}}"
        path = arxiv_fetch.fetch_by_bibtex(bibtex, dest=tmp_workspace)
        assert path.exists()
