import pytest
from paper_intensive_reading.render_formula import render
from paper_intensive_reading.errors import ParseError


def test_render_simple_latex(tmp_path):
    out = tmp_path / "eq.png"
    path = render(r"\frac{a}{b}", out_path=out, fontsize=20)
    assert path == out
    assert path.exists()
    assert path.stat().st_size > 500


def test_render_complex_latex(tmp_path):
    out = tmp_path / "attn.png"
    latex = r"\text{Attention}(Q,K,V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V"
    path = render(latex, out_path=out, fontsize=18)
    assert path.exists()
    assert path.stat().st_size > 1000


def test_render_invalid_latex_raises(tmp_path):
    out = tmp_path / "err.png"
    with pytest.raises(ParseError):
        render(r"\frac{", out_path=out)


def test_render_with_color(tmp_path):
    out = tmp_path / "colored.png"
    path = render(r"E = mc^2", out_path=out, color="blue")
    assert path.exists()


class TestBatchRender:
    def test_render_multiple(self, tmp_path):
        from paper_intensive_reading.render_formula import render_batch

        formulas = [
            ("eq-1", r"E = mc^2"),
            ("eq-2", r"a^2 + b^2 = c^2"),
            ("eq-3", r"\sum_{i=1}^{n} x_i"),
        ]
        paths = render_batch(formulas, out_dir=tmp_path)
        assert len(paths) == 3
        assert all(p.exists() for p in paths.values())
        assert "eq-1" in paths

    def test_batch_skip_failures(self, tmp_path):
        from paper_intensive_reading.render_formula import render_batch

        formulas = [
            ("good", r"x = 1"),
            ("bad", r"\frac{"),
        ]
        paths = render_batch(formulas, out_dir=tmp_path, skip_failures=True)
        assert "good" in paths
        assert "bad" not in paths
