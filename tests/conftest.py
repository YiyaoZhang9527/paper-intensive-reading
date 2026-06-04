import os
import tempfile
import shutil
from pathlib import Path
import pytest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_workspace():
    """隔离的临时工作目录，自动清理。"""
    path = Path(tempfile.mkdtemp(prefix="paper-test-"))
    old_cwd = os.getcwd()
    os.chdir(path)
    yield path
    os.chdir(old_cwd)
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def tmp_db(tmp_workspace):
    return str(tmp_workspace / "test.sqlite")


@pytest.fixture
def sample_paper_dict():
    return {
        "arxiv_id": "2302.13971",
        "title": "LLaMA: Open and Efficient Foundation Language Models",
        "authors": ["Touvron", "Lavril", "Izacard"],
        "affiliations": ["Meta AI"],
        "abstract": "We introduce LLaMA.",
        "published": "2023-02-27",
        "pdf_path": "/tmp/2302.13971.pdf",
        "sections": [{
            "number": "1", "title": "Introduction", "level": 1,
            "paragraphs": [{"text": "Foundation models are large.", "page": 1}],
            "formulas": [],
        }],
        "figures": [{"number": "Figure 1", "caption": "Overview.",
                     "image_path": "/tmp/fig-1.png", "page": 3}],
        "tables": [], "algorithms": [], "references": [],
    }
