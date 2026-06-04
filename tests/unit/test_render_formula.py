import pytest
from pathlib import Path
from paper_intensive_reading.render_formula import render, render_to_png
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
