"""用 matplotlib mathtext 把 LaTeX 渲染为 PNG。"""
import tempfile
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .errors import ParseError


def render(
    latex: str, out_path: Path, fontsize: int = 20,
    color: str = "black", dpi: int = 200, pad: float = 0.3,
) -> Path:
    """把 LaTeX 公式渲染为 PNG。"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.axis("off")
        text = ax.text(0.5, 0.5, f"${latex}$", fontsize=fontsize,
                       color=color, ha="center", va="center")
        fig.canvas.draw()
        bbox = text.get_window_extent()
        width = (bbox.width + 40) / dpi
        height = (bbox.height + 40) / dpi
        fig.set_size_inches(width, height)
        text.set_position((0.5, 0.5))
        fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight",
                    pad_inches=pad, transparent=True)
        plt.close(fig)
    except Exception as e:
        raise ParseError("default", latex=latex[:50], detail=str(e)) from e

    if not out_path.exists() or out_path.stat().st_size < 100:
        raise ParseError("default", latex=latex[:50], detail="生成图片为空")
    return out_path


def render_to_png(latex: str, **kwargs) -> bytes:
    """返回 PNG 字节流。"""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp = Path(f.name)
    try:
        render(latex, out_path=tmp, **kwargs)
        return tmp.read_bytes()
    finally:
        if tmp.exists():
            tmp.unlink()


def render_batch(
    formulas: list[tuple[str, str]], out_dir: Path,
    skip_failures: bool = True, **render_kwargs,
) -> dict[str, Path]:
    """批量渲染公式。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, Path] = {}
    for name, latex in formulas:
        out_path = out_dir / f"{name}.png"
        try:
            render(latex, out_path=out_path, **render_kwargs)
            results[name] = out_path
        except ParseError:
            if not skip_failures:
                raise
    return results
