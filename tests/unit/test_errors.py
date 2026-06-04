import pytest
from paper_intensive_reading.errors import (
    PaperReadError, FetchError, ParseError, NumPyRunError,
    ObsidianError, NotionError, LLMError, get_user_message,
)


def test_error_hierarchy():
    assert issubclass(FetchError, PaperReadError)
    assert issubclass(ParseError, PaperReadError)
    assert issubclass(NumPyRunError, PaperReadError)


def test_fetch_error_subtypes():
    err = FetchError("arxiv_404", arxiv_id="0000.00000")
    msg = get_user_message(err)
    assert "0000.00000" in msg


def test_parse_error_subtypes():
    err = ParseError("encrypted")
    msg = get_user_message(err)
    assert "加密" in msg


def test_numpy_error_with_detail():
    err = NumPyRunError("syntax", detail="unexpected indent")
    msg = get_user_message(err)
    assert "unexpected indent" in msg


def test_obsidian_error_with_path():
    err = ObsidianError("no_vault", vault_path="/tmp/vault")
    msg = get_user_message(err)
    assert "/tmp/vault" in msg


def test_notion_error_rate_limit():
    err = NotionError("rate_limit")
    msg = get_user_message(err)
    assert "限流" in msg or "rate" in msg.lower()


def test_llm_error_content_filter():
    err = LLMError("content_filter")
    msg = get_user_message(err)
    assert "敏感" in msg or "filter" in msg.lower()


def test_unknown_error_fallback():
    err = PaperReadError("totally_unknown_subtype")
    msg = get_user_message(err)
    assert msg and len(msg) > 0
