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
