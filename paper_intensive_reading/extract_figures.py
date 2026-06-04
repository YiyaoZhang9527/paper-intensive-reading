"""从 PDF 抠图或渲染页区域。"""
from pathlib import Path
import fitz


def extract_embedded_images(pdf_path: Path, out_dir: Path) -> list[str]:
    """提取 PDF 内嵌的栅格图像。"""
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            page = doc[page_idx]
            images = page.get_images(full=True)
            for img_idx, img in enumerate(images):
                xref = img[0]
                try:
                    pix = fitz.Pixmap(doc, xref)
                    out_path = out_dir / f"page{page_idx+1}-img{img_idx+1}.png"
                    if pix.n - pix.alpha >= 4:  # CMYK
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    pix.save(str(out_path))
                    paths.append(str(out_path))
                except Exception:
                    continue
    return paths


def render_page_region(pdf_path: Path, page_num: int, out_path: Path, dpi: int = 200) -> Path:
    """把 PDF 的某一页渲染为 PNG。"""
    pdf_path = Path(pdf_path)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as doc:
        if page_num >= doc.page_count:
            raise ValueError(f"Page {page_num} not in {pdf_path}")
        page = doc[page_num]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        pix.save(str(out_path))
    return out_path


def attach_images_to_figures(
    pdf_path: Path, figures: list, out_dir: Path,
) -> list[str]:
    """提取所有图，把路径挂到 figure.image_path。"""
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    extra_dir = out_dir / "extra"
    extra_dir.mkdir(parents=True, exist_ok=True)

    all_extracted = extract_embedded_images(pdf_path, out_dir)
    by_page: dict[int, list[str]] = {}
    for p in all_extracted:
        fname = Path(p).stem
        try:
            page_num = int(fname.split("-")[0].replace("page", ""))
        except (ValueError, IndexError):
            continue
        by_page.setdefault(page_num, []).append(p)

    used: set[str] = set()
    for fig in figures:
        page_imgs = by_page.get(fig.page + 1, [])
        for img_path in page_imgs:
            if img_path in used:
                continue
            fig.image_path = img_path
            used.add(img_path)
            break
        if not fig.image_path and page_imgs:
            fig.image_path = page_imgs[0]
            used.add(page_imgs[0])

    extra = [p for p in all_extracted if p not in used]
    return extra
