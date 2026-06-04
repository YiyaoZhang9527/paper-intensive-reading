import pytest
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
