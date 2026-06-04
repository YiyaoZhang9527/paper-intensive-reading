import pytest
from pathlib import Path
from paper_intensive_reading.image_gen import (
    generate, generate_ascii_fallback, PROVIDERS
)


class TestAsciiFallback:
    def test_simple_text_to_ascii(self):
        result = generate_ascii_fallback("Hello")
        assert "Hello" in result or "|" in result

    def test_diagram_attention(self):
        result = generate_ascii_fallback("Q -> K -> V")
        assert "Q" in result
        assert "K" in result
        assert "V" in result


class TestGenerate:
    def test_generate_falls_back_to_ascii(self, tmp_path, monkeypatch):
        from paper_intensive_reading import image_gen
        monkeypatch.setattr(image_gen, "PROVIDERS", [])  # 没有任何 provider

        out = tmp_path / "out.txt"
        result = generate("some prompt", out_path=out)
        # ascii fallback 返回字符串
        assert isinstance(result, str)

    def test_generate_uses_first_working_provider(self, tmp_path, monkeypatch):
        from paper_intensive_reading import image_gen

        called = []

        def fake_provider_1(prompt, out_path):
            called.append("p1")
            raise RuntimeError("provider 1 down")

        def fake_provider_2(prompt, out_path):
            called.append("p2")
            out_path.write_text("FAKE_IMAGE")
            return str(out_path)

        monkeypatch.setattr(image_gen, "PROVIDERS", [fake_provider_1, fake_provider_2])

        out = tmp_path / "out.png"
        result = generate("test", out_path=out)
        assert called == ["p1", "p2"]
        assert "FAKE_IMAGE" in out.read_text()


def test_providers_list_exists():
    assert isinstance(PROVIDERS, list)
