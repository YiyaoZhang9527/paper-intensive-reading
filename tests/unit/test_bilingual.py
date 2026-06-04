import pytest
from paper_intensive_reading.bilingual import (
    translate, build_glossary, KNOWN_TERMS
)


class TestTranslate:
    def test_known_term(self):
        result = translate("attention")
        assert "zh" in result
        assert result["zh"] in ["注意力", "关注", "注意力机制"]

    def test_case_insensitive(self):
        result = translate("Attention")
        assert "zh" in result

    def test_unknown_term_returns_en(self):
        result = translate("xyz-abc-12345-unknown")
        assert result["zh"]

    def test_embedding_translation(self):
        result = translate("embedding")
        assert "嵌入" in result["zh"]

    def test_fine_tuning_translation(self):
        result = translate("fine-tuning")
        assert "微调" in result["zh"]


class TestBuildGlossary:
    def test_build_from_terms(self):
        terms = ["attention", "embedding", "transformer"]
        glossary = build_glossary(terms)
        assert "attention" in glossary
        assert "embedding" in glossary
        assert "transformer" in glossary
        assert all("zh" in v for v in glossary.values())

    def test_build_with_descriptions(self):
        glossary = build_glossary(["attention"], with_description=True)
        assert glossary["attention"]["description"]

    def test_dedup(self):
        terms = ["attention", "Attention", "ATTENTION"]
        glossary = build_glossary(terms)
        assert len(glossary) == 1


def test_known_terms_not_empty():
    assert len(KNOWN_TERMS) > 30
