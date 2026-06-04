import pytest
from paper_intensive_reading.to_obsidian import (
    detect_vault, prepare_vault_dir
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


class TestCopyToVault:
    def test_copy_md_and_pdf(self, tmp_path):
        from paper_intensive_reading.to_obsidian import copy_to_vault

        vault = tmp_path / "vault"
        vault.mkdir()
        paper_dir = vault / "Papers" / "2302.13971-LLaMA"
        paper_dir.mkdir(parents=True)
        figures_dir = paper_dir / "figures"
        figures_dir.mkdir()

        # 准备源文件
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        md_file = src_dir / "note.md"
        md_file.write_text("# LLaMA\n\nContent")
        pdf_file = src_dir / "2302.13971.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%fake\n")
        fig_file = src_dir / "fig-1.png"
        fig_file.write_bytes(b"PNG_FAKE")

        copy_to_vault(
            paper_dir=paper_dir,
            md_path=md_file,
            pdf_path=pdf_file,
            figure_paths=[fig_file],
        )

        assert (paper_dir / "2302.13971-精读笔记.md").exists()
        assert (paper_dir / "2302.13971.pdf").exists()
        assert (figures_dir / "fig-1.png").exists()

    def test_update_wikilinks(self, tmp_path):
        from paper_intensive_reading.to_obsidian import add_wikilinks

        md = tmp_path / "note.md"
        md.write_text("# Note\n\nSome text [[GLOBAL_NOTE]] more text.\n\nFinal [[ANOTHER_NOTE]].\n")
        # 注入 vault 内链接
        # add_wikilinks 寻找 arxiv_id 开头的目录，需要先创建
        (tmp_path / "2302.13971-LLaMA").mkdir()
        add_wikilinks(md, "2302.13971", ["GLOBAL_NOTE", "ANOTHER_NOTE"])
        content = md.read_text()
        assert "[[2302.13971-LLaMA/2302.13971-精读笔记|GLOBAL_NOTE]]" in content or "[[2302.13971" in content


class TestSaveUnified:
    def test_save_end_to_end(self, tmp_path):
        from paper_intensive_reading.to_obsidian import save

        # 设置 vault
        vault = tmp_path / "vault"
        vault.mkdir()

        # 准备源文件
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        md_file = src_dir / "2302.13971-精读笔记.md"
        md_file.write_text("# LLaMA\n\nTest")
        pdf_file = src_dir / "2302.13971.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%fake\n")

        save(
            arxiv_id="2302.13971",
            title="LLaMA",
            md_path=md_file,
            pdf_path=pdf_file,
            vault_path=vault,
        )

        assert (vault / "Papers" / "2302.13971-LLaMA" / "2302.13971-精读笔记.md").exists()
        assert (vault / "Papers" / "2302.13971-LLaMA" / "2302.13971.pdf").exists()
        # 索引页
        index = vault / "Papers" / "_index.md"
        assert index.exists()
        assert "2302.13971" in index.read_text()


class TestIndexPage:
    def test_update_index_appends(self, tmp_path):
        from paper_intensive_reading.to_obsidian import update_index
        vault = tmp_path / "vault"
        vault.mkdir()
        paper_dir = vault / "Papers" / "2302.13971-LLaMA"
        paper_dir.mkdir(parents=True)
        (paper_dir / "2302.13971-精读笔记.md").write_text("# LLaMA")

        update_index(vault, "2302.13971", "LLaMA")
        update_index(vault, "2304.08485", "QLoRA")

        index = (vault / "Papers" / "_index.md").read_text()
        assert "2302.13971" in index
        assert "2304.08485" in index
