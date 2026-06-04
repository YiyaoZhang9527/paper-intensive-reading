import os
import pytest
from pathlib import Path
from paper_intensive_reading.to_obsidian import (
    detect_vault, prepare_vault_dir, OBSIDIAN_CONFIG_KEY
)
from paper_intensive_reading.errors import ObsidianError


class TestDetectVault:
    def test_detect_from_env(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
        vault = detect_vault()
        assert vault == tmp_path

    def test_detect_from_config_file(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        config = tmp_path / ".paper-skill.json"
        config.write_text(f'{{"obsidian_vault": "{tmp_path}"}}')
        monkeypatch.chdir(tmp_path)
        vault = detect_vault()
        assert vault == tmp_path

    def test_detect_no_vault_raises(self, monkeypatch, tmp_path):
        monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
        monkeypatch.chdir(tmp_path)
        # 确保 .paper-skill.json 不存在
        if (tmp_path / ".paper-skill.json").exists():
            (tmp_path / ".paper-skill.json").unlink()
        with pytest.raises(ObsidianError) as exc:
            detect_vault()
        assert exc.value.subtype == "no_vault"


class TestPrepareVaultDir:
    def test_create_paper_folder(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        paper_dir = prepare_vault_dir(vault, "2302.13971", "LLaMA")
        assert paper_dir.exists()
        assert paper_dir.name == "2302.13971-LLaMA"
        assert paper_dir.parent.name == "Papers"

    def test_existing_dir_not_recreated(self, tmp_path):
        vault = tmp_path / "vault"
        vault.mkdir()
        existing = vault / "Papers" / "2302.13971-LLaMA"
        existing.mkdir(parents=True)
        (existing / "existing.txt").write_text("keep me")

        paper_dir = prepare_vault_dir(vault, "2302.13971", "LLaMA")
        assert (paper_dir / "existing.txt").exists()  # 保留原文件
