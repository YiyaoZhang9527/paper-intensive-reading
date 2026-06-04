"""同步到 Obsidian vault。"""
import os
import json
import shutil
from pathlib import Path
from .errors import ObsidianError


OBSIDIAN_CONFIG_KEY = "obsidian_vault"


def detect_vault() -> Path:
    """检测 Obsidian vault 路径。优先级：环境变量 > .paper-skill.json > 默认 ~/Documents/ObsidianVault。"""
    env_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_path:
        p = Path(env_path).expanduser()
        if p.exists():
            return p

    config_file = Path.cwd() / ".paper-skill.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            if OBSIDIAN_CONFIG_KEY in config:
                p = Path(config[OBSIDIAN_CONFIG_KEY]).expanduser()
                if p.exists():
                    return p
        except Exception:
            pass

    default = Path.home() / "Documents" / "ObsidianVault"
    if default.exists():
        return default

    raise ObsidianError("no_vault", vault_path=str(default))


def prepare_vault_dir(vault: Path, arxiv_id: str, title: str) -> Path:
    """在 vault/Papers/ 下创建论文文件夹，返回路径。已存在则不重建。"""
    vault = Path(vault)
    # 清理 title 为安全的文件夹名
    safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in title)[:50].strip()
    folder_name = f"{arxiv_id}-{safe_title}" if safe_title else arxiv_id
    paper_dir = vault / "Papers" / folder_name
    paper_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = paper_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    return paper_dir


def copy_to_vault(
    paper_dir: Path, md_path: Path, pdf_path: Path | None = None,
    figure_paths: list[Path] | None = None,
) -> dict[str, Path | list[Path]]:
    """复制 MD + PDF + 图片到 vault，返回产物路径字典。"""
    paper_dir = Path(paper_dir)
    md_path = Path(md_path)
    figure_paths = figure_paths or []

    arxiv_id = paper_dir.name.split("-")[0]
    target_md = paper_dir / f"{arxiv_id}-精读笔记.md"
    shutil.copy2(md_path, target_md)

    result: dict[str, Path | list[Path]] = {"md": target_md}

    if pdf_path and Path(pdf_path).exists():
        target_pdf = paper_dir / f"{arxiv_id}.pdf"
        shutil.copy2(pdf_path, target_pdf)
        result["pdf"] = target_pdf

    figures_dir = paper_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    copied_figs: list[Path] = []
    for fig in figure_paths:
        if not Path(fig).exists():
            continue
        target = figures_dir / Path(fig).name
        shutil.copy2(fig, target)
        copied_figs.append(target)
    result["figures"] = copied_figs

    return result


def add_wikilinks(md_path: Path, arxiv_id: str, link_names: list[str]) -> None:
    """把 [[NAME]] 替换为 [[arxiv-id-LLaMA/...|NAME]] 双向链接。"""
    md_path = Path(md_path)
    content = md_path.read_text()
    folder_name = None
    # 找到对应的文件夹名
    if md_path.parent.exists():
        for child in md_path.parent.iterdir():
            if child.is_dir() and child.name.startswith(arxiv_id):
                folder_name = child.name
                break

    if not folder_name:
        return  # 没找到对应文件夹，不处理

    for name in link_names:
        old = f"[[{name}]]"
        new = f"[[{folder_name}/{md_path.name}|{name}]]"
        content = content.replace(old, new)

    md_path.write_text(content)


def update_index(vault: Path, arxiv_id: str, title: str) -> None:
    """更新 Papers/_index.md。"""
    vault = Path(vault)
    index_path = vault / "Papers" / "_index.md"
    if not index_path.exists():
        index_path.write_text("# Papers Index\n\n| arXiv ID | 标题 | 笔记 |\n|---|---|---|\n")
    content = index_path.read_text()
    if arxiv_id in content:
        return  # 已存在，不重复添加
    line = f"| [{arxiv_id}]({arxiv_id}-{title}/{arxiv_id}-精读笔记.md) | {title} | [[笔记]] |\n"
    index_path.write_text(content + line)


def save(
    arxiv_id: str, title: str, md_path: Path, pdf_path: Path | None = None,
    figure_paths: list[Path] | None = None, vault_path: Path | None = None,
) -> dict[str, Path | list[Path]]:
    """统一入口：保存到 Obsidian vault。"""
    vault = vault_path or detect_vault()
    paper_dir = prepare_vault_dir(vault, arxiv_id, title)
    result = copy_to_vault(paper_dir, md_path, pdf_path, figure_paths)
    update_index(vault, arxiv_id, title)
    return result
