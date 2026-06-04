# 论文精读 Skill 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 AI/ML 论文对话式精读 skill，从 arXiv 自动下载 PDF、用小学数学基础讲清每个公式（带 NumPy 实际运行 + 三对照验证）、强制做理解确认循环、沉淀笔记到本地 MD / Obsidian / Notion 三端。

**Architecture:** 单一 SKILL.md 对话入口 + 15 个 Python 脚本（每个职责单一、可独立测试）。NumPy 代码运行带 AST 沙箱；PDF 解析拒绝 JavaScript/宏；arXiv 输入正则校验。所有持久化用 SQLite + 落盘文件，幂等同步。

**Tech Stack:** Python 3.11+, pytest, uv, PyMuPDF (fitz), pikepdf, pdfplumber, numpy, matplotlib (mathtext), requests, arxiv API, python-dotenv, bibtexparser, sqlite3 (stdlib)

**Spec 文档：** `docs/superpowers/specs/2026-06-04-paper-intensive-reading-design.md`

---

## 阶段总览

| 阶段 | 内容 | 任务数 | 计划文件 |
|------|------|--------|---------|
| P1 | 项目骨架 + 数据模型 + 错误体系 | T1.1-T1.4 | 本文件 §1 |
| P2 | 论文获取 (arxiv_fetch) | T2.1-T2.5 | 本文件 §2 |
| P3 | 论文解析 (pdf_parse) | T3.1-T3.5 | 本文件 §3 |
| P4 | 图表提取 (extract_figures) | T4.1-T4.2 | 本文件 §4 |
| P5 | 公式渲染 (render_formula) | T5.1-T5.2 | 本文件 §5 |
| P6 | NumPy 沙箱 (numpy_runner) | T6.1-T6.5 | 本文件 §6 |
| P7 | 概念阶梯 + 术语 (math_ladder + bilingual) | T7.1-T7.4 | 本文件 §7 |
| P8 | 公式讲解 6 段引擎 (formula_explainer) | T8.1-T8.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §8 |
| P9 | 阅读清单存储 (paper_store) | T9.1-T9.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §9 |
| P10 | 笔记渲染 (to_markdown) | T10.1-T10.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §10 |
| P11 | Obsidian 同步 (to_obsidian) | T11.1-T11.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §11 |
| P12 | Notion 同步 (to_notion) | T12.1-T12.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §12 |
| P13 | 图像生成 fallback (image_gen) | T13.1-T13.3 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §13 |
| P14 | 调研模式 (survey) | T14.1-T14.2 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §14 |
| P15 | 对比模式 (compare) | T15.1-T15.2 | [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) §15 |
| P16 | 主入口 SKILL.md | T16.1-T16.3 | [plan-part-3.md](2026-06-04-paper-intensive-reading-PLAN-part3.md) §16 |
| P17 | 端到端 + 性能 + 安全 | T17.1-T17.3 | [plan-part-3.md](2026-06-04-paper-intensive-reading-PLAN-part3.md) §17 |

---

# 阶段 P1：项目骨架

## Task 1.1: 项目初始化

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `README.md`, `paper-intensive-reading/__init__.py`, 目录结构

- [ ] **Step 1: 创建目录结构**

```bash
cd /Users/zhangjing/Documents/论文精度
mkdir -p paper-intensive-reading tests/unit tests/integration tests/e2e tests/snapshots tests/safety tests/fixtures references data
```

- [ ] **Step 2: 写 pyproject.toml**

```toml
[project]
name = "paper-intensive-reading"
version = "0.1.0"
description = "对话式论文精读 skill"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31.0",
    "arxiv>=2.1.0",
    "pymupdf>=1.24.0",
    "pikepdf>=8.13.0",
    "pdfplumber>=0.10.0",
    "numpy>=1.26.0",
    "matplotlib>=3.8.0",
    "python-dotenv>=1.0.0",
    "bibtexparser>=1.4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.4.0",
    "mypy>=1.8.0",
    "bandit>=1.7.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["paper-intensive-reading"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
    "safety: marks safety/security tests",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true
```

- [ ] **Step 3: 写 .gitignore**

```gitignore
__pycache__/
*.py[cod]
.venv/
.env
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage

data/papers/pdfs/*.pdf
data/papers/notes/*.md
data/papers/drafts/*.md
data/papers/figures/
data/papers/formulas/
data/papers/logs/
data/cache/
data/reading-list.sqlite
data/reading-list.sqlite-journal

!tests/fixtures/
```

- [ ] **Step 4: 写 README.md + __init__.py**

`README.md`:
```markdown
# Paper Intensive Reading Skill
对话式 AI/ML 论文精读工具。
详见 [设计文档](docs/superpowers/specs/2026-06-04-paper-intensive-reading-design.md)。
```

`paper-intensive-reading/__init__.py`:
```python
"""Paper Intensive Reading Skill."""
__version__ = "0.1.0"
```

- [ ] **Step 5: 初始化 git 并提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git init
uv sync
git add .
git commit -m "chore: initialize project skeleton"
```

---

## Task 1.2: 数据模型 types.py

**Files:**
- Create: `paper-intensive-reading/types.py`
- Test: `tests/unit/test_types.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_types.py`:
```python
import pytest
from datetime import date
from paper_intensive_reading.types import (
    Paper, Section, Formula, Figure, Table, Algorithm, Paragraph
)


def test_paper_creation():
    paper = Paper(
        arxiv_id="2302.13971",
        title="LLaMA: Open and Efficient Foundation Language Models",
        authors=["Touvron", "Lavril"],
        affiliations=["Meta AI"],
        abstract="We introduce LLaMA.",
        published=date(2023, 2, 27),
        pdf_path="/tmp/2302.13971.pdf",
        sections=[], figures=[], tables=[], algorithms=[], references=[],
    )
    assert paper.arxiv_id == "2302.13971"


def test_paper_to_dict():
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    d = paper.to_dict()
    assert d["arxiv_id"] == "2302.13971"
    assert d["published"] == "2023-02-27"


def test_paper_from_dict_roundtrip():
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    d = paper.to_dict()
    paper2 = Paper.from_dict(d)
    assert paper2.arxiv_id == paper.arxiv_id
    assert paper2.title == paper.title


def test_formula_creation():
    f = Formula(
        number="(1)",
        latex=r"\text{RMSNorm}(x) = \frac{x}{\sqrt{\text{Mean}(x^2)}} \cdot \gamma",
        context_before="We use RMSNorm.", context_after="It stabilizes.",
        symbols={"x": "input", "gamma": "scale"},
    )
    assert f.number == "(1)"


def test_figure_creation():
    fig = Figure(number="Figure 1", caption="Overview", image_path="/tmp/fig-1.png", page=3)
    assert fig.page == 3
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_types.py -v
```
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 写 types.py**

`paper-intensive-reading/types.py`:
```python
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any


@dataclass
class Paragraph:
    text: str
    page: int


@dataclass
class Formula:
    number: str
    latex: str
    context_before: str
    context_after: str
    symbols: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Section:
    number: str
    title: str
    level: int
    paragraphs: list[Paragraph] = field(default_factory=list)
    formulas: list[Formula] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "level": self.level,
            "paragraphs": [{"text": p.text, "page": p.page} for p in self.paragraphs],
            "formulas": [f.to_dict() for f in self.formulas],
        }


@dataclass
class Figure:
    number: str
    caption: str
    image_path: str
    page: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Table:
    number: str
    caption: str
    headers: list[str]
    rows: list[list[str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Algorithm:
    number: str
    title: str
    pseudocode: str
    language_hint: str = "pseudocode"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Reference:
    raw: str
    arxiv_id: str | None = None
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    affiliations: list[str]
    abstract: str
    published: date
    pdf_path: str
    sections: list[Section] = field(default_factory=list)
    figures: list[Figure] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    algorithms: list[Algorithm] = field(default_factory=list)
    references: list[Reference] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": list(self.authors),
            "affiliations": list(self.affiliations),
            "abstract": self.abstract,
            "published": self.published.isoformat(),
            "pdf_path": self.pdf_path,
            "sections": [s.to_dict() for s in self.sections],
            "figures": [f.to_dict() for f in self.figures],
            "tables": [t.to_dict() for t in self.tables],
            "algorithms": [a.to_dict() for a in self.algorithms],
            "references": [r.to_dict() for r in self.references],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Paper":
        return cls(
            arxiv_id=d["arxiv_id"],
            title=d["title"],
            authors=d["authors"],
            affiliations=d["affiliations"],
            abstract=d["abstract"],
            published=date.fromisoformat(d["published"]),
            pdf_path=d["pdf_path"],
            sections=[
                Section(
                    number=s["number"], title=s["title"], level=s["level"],
                    paragraphs=[Paragraph(**p) for p in s["paragraphs"]],
                    formulas=[Formula(**f) for f in s["formulas"]],
                ) for s in d.get("sections", [])
            ],
            figures=[Figure(**f) for f in d.get("figures", [])],
            tables=[Table(**t) for t in d.get("tables", [])],
            algorithms=[Algorithm(**a) for a in d.get("algorithms", [])],
            references=[Reference(**r) for r in d.get("references", [])],
        )
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_types.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/types.py tests/unit/test_types.py
git commit -m "feat(types): add core data models (Paper, Section, Formula, Figure, Table, Algorithm, Reference)"
```

---

## Task 1.3: 错误体系 errors.py

**Files:**
- Create: `paper-intensive-reading/errors.py`
- Test: `tests/unit/test_errors.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_errors.py`:
```python
import pytest
from paper_intensive_reading.errors import (
    PaperReadError, FetchError, ParseError, NumPyRunError,
    ObsidianError, NotionError, LLMError, get_user_message,
)


def test_error_hierarchy():
    assert issubclass(FetchError, PaperReadError)
    assert issubclass(ParseError, PaperReadError)
    assert issubclass(NumPyRunError, PaperReadError)


def test_fetch_error_subtypes():
    err = FetchError("arxiv_404", arxiv_id="0000.00000")
    msg = get_user_message(err)
    assert "0000.00000" in msg


def test_parse_error_subtypes():
    err = ParseError("encrypted")
    msg = get_user_message(err)
    assert "加密" in msg


def test_numpy_error_with_detail():
    err = NumPyRunError("syntax", detail="unexpected indent")
    msg = get_user_message(err)
    assert "unexpected indent" in msg


def test_obsidian_error_with_path():
    err = ObsidianError("no_vault", vault_path="/tmp/vault")
    msg = get_user_message(err)
    assert "/tmp/vault" in msg


def test_notion_error_rate_limit():
    err = NotionError("rate_limit")
    msg = get_user_message(err)
    assert "限流" in msg or "rate" in msg.lower()


def test_llm_error_content_filter():
    err = LLMError("content_filter")
    msg = get_user_message(err)
    assert "敏感" in msg or "filter" in msg.lower()


def test_unknown_error_fallback():
    err = PaperReadError("totally_unknown_subtype")
    msg = get_user_message(err)
    assert msg and len(msg) > 0
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_errors.py -v
```

- [ ] **Step 3: 写 errors.py**

`paper-intensive-reading/errors.py`:
```python
from typing import Any


class PaperReadError(Exception):
    """所有 skill 内错误的基类。"""
    def __init__(self, subtype: str, **context: Any):
        self.subtype = subtype
        self.context = context
        super().__init__(f"{type(self).__name__}[{subtype}]")


class FetchError(PaperReadError): pass
class ParseError(PaperReadError): pass
class NumPyRunError(PaperReadError): pass
class ObsidianError(PaperReadError): pass
class NotionError(PaperReadError): pass
class LLMError(PaperReadError): pass


_MESSAGES: dict[type, dict[str, str]] = {
    FetchError: {
        "arxiv_404": "arXiv 上找不到这篇论文（ID: {arxiv_id}）。请检查 ID 是否正确，或传本地 PDF 路径。",
        "arxiv_timeout": "arXiv 下载超时（已重试 3 次）。可能是网络问题，可稍后重试或换成本地 PDF。",
        "arxiv_503": "arXiv 服务暂时不可用。请 5 分钟后重试。",
        "rate_limit": "arXiv 限流了（每分钟最多 30 次）。请等 1 分钟。",
        "invalid_pdf": "下载的文件不是有效 PDF。可能 arXiv 链接变了，请改用 PDF 链接或本地路径。",
        "default": "下载论文失败：{subtype}。请检查输入或网络。",
    },
    ParseError: {
        "encrypted": "PDF 是加密的，skill 无法读取。请提供未加密的版本。",
        "scan_only": "PDF 是扫描件（图片），没有可解析文字。skill 暂不支持 OCR，请提供文字版 PDF。",
        "no_sections": "PDF 解析成功但没识别出章节结构（可能是非标准格式）。skill 会按页处理，但可能不准。",
        "no_formulas": "PDF 里没识别到公式（可能用图片或纯文字描述）。公式讲解部分会跳过。",
        "dangerous": "PDF 包含可执行动作（JavaScript/宏），出于安全拒绝处理。",
        "default": "PDF 解析失败：{subtype}。",
    },
    NumPyRunError: {
        "syntax": "代码有语法错误：{detail}。我会简化例子再试。",
        "runtime": "代码运行时报错：{detail}。我会改用 d=2 的极简例子。",
        "timeout": "代码运行超过 10 秒（可能计算量太大）。我换更小例子。",
        "memory": "代码占用内存过多。我换更小维度。",
        "forbidden_import": "代码包含禁止的导入：{detail}。只允许 import numpy。",
        "forbidden_name": "代码包含禁止的操作：{detail}。",
        "default": "NumPy 代码运行失败：{subtype}。",
    },
    ObsidianError: {
        "no_vault": "找不到 Obsidian vault（路径：{vault_path}）。请检查配置，或跳过 Obsidian 同步。",
        "permission": "Obsidian vault 没有写权限。",
        "sync_fail": "Obsidian 同步失败（已重试 3 次）：{detail}",
        "default": "Obsidian 同步失败：{subtype}。",
    },
    NotionError: {
        "no_api_key": "Notion API key 未配置。请设置环境变量 NOTION_API_KEY，或跳过 Notion 同步。",
        "no_db": "找不到 Notion 数据库（ID: {db_id}）。请检查配置。",
        "rate_limit": "Notion API 限流（每秒 3 次）。我已加入重试队列。",
        "file_too_big": "PDF 太大（> 100MB），Notion 单次上传有限制。我跳过 PDF 上传，只同步笔记。",
        "default": "Notion 同步失败：{subtype}。",
    },
    LLMError: {
        "rate_limit": "AI 接口限流，我会等 30 秒后重试。",
        "content_filter": "AI 拒绝生成内容（可能涉及敏感话题）。我会换种问法。",
        "bad_format": "AI 返回格式不对（缺段、JSON 解析失败）。我重新生成。",
        "default": "AI 调用失败：{subtype}。",
    },
}


def get_user_message(err: PaperReadError) -> str:
    table = _MESSAGES.get(type(err), {})
    template = table.get(err.subtype, table.get("default", "出错了：{subtype}"))
    try:
        return template.format(subtype=err.subtype, **err.context)
    except KeyError:
        return f"{type(err).__name__}[{err.subtype}]: {err.context}"
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_errors.py -v
```
Expected: 8 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/errors.py tests/unit/test_errors.py
git commit -m "feat(errors): add PaperReadError hierarchy and Chinese error messages"
```

---

## Task 1.4: conftest.py 公共 fixtures

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: 写 conftest.py**

`tests/conftest.py`:
```python
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
```

- [ ] **Step 2: 验证 conftest 可加载**

```bash
cd /Users/zhangjing/Documents/论文精度
touch tests/fixtures/__init__.py
uv run pytest --collect-only tests/ 2>&1 | head -20
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add tests/conftest.py tests/fixtures/__init__.py
git commit -m "test: add conftest.py with shared fixtures"
```

---

# 阶段 P2：论文获取 (arxiv_fetch)

## Task 2.1: arxiv_fetch - ID 验证 + URL 解析

**Files:**
- Create: `paper-intensive-reading/arxiv_fetch.py`
- Test: `tests/unit/test_arxiv_fetch.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_arxiv_fetch.py`:
```python
import pytest
from paper_intensive_reading.arxiv_fetch import (
    validate_arxiv_id, normalize_arxiv_id, extract_id_from_url
)
from paper_intensive_reading.errors import FetchError


class TestValidateArxivId:
    def test_valid_id(self):
        assert validate_arxiv_id("2302.13971") is True

    def test_valid_id_with_version(self):
        assert validate_arxiv_id("2302.13971v1") is True
        assert validate_arxiv_id("2302.13971v3") is True

    def test_invalid_id_letters(self):
        with pytest.raises(FetchError) as exc:
            validate_arxiv_id("abc.def")
        assert exc.value.subtype == "arxiv_404"

    def test_invalid_id_too_short(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("2302.139")

    def test_invalid_id_too_long(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("2302.139711234")

    def test_empty_id(self):
        with pytest.raises(FetchError):
            validate_arxiv_id("")


class TestNormalizeArxivId:
    def test_strip_version(self):
        assert normalize_arxiv_id("2302.13971v2") == "2302.13971"

    def test_no_version(self):
        assert normalize_arxiv_id("2302.13971") == "2302.13971"

    def test_uppercase(self):
        assert normalize_arxiv_id("2302.13971V2") == "2302.13971"


class TestExtractIdFromUrl:
    def test_abs_url(self):
        assert extract_id_from_url("https://arxiv.org/abs/2302.13971") == "2302.13971"

    def test_pdf_url(self):
        assert extract_id_from_url("https://arxiv.org/pdf/2302.13971") == "2302.13971"

    def test_pdf_url_with_version(self):
        assert extract_id_from_url("https://arxiv.org/pdf/2302.13971v2.pdf") == "2302.13971v2"

    def test_invalid_url(self):
        with pytest.raises(FetchError):
            extract_id_from_url("https://example.com/not-an-arxiv")
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```

- [ ] **Step 3: 写 arxiv_fetch.py 第一部分**

`paper-intensive-reading/arxiv_fetch.py`:
```python
"""从多个来源获取论文 PDF。"""
import re
from pathlib import Path
from datetime import date

import arxiv
import requests

from .errors import FetchError
from .types import Paper

ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
ARXIV_URL_PATTERN = re.compile(
    r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)(?:\.pdf)?"
)


def validate_arxiv_id(arxiv_id: str) -> bool:
    """验证 arXiv ID 格式。失败抛 FetchError(arxiv_404)。"""
    if not arxiv_id or not ARXIV_ID_PATTERN.match(arxiv_id):
        raise FetchError("arxiv_404", arxiv_id=arxiv_id)
    return True


def normalize_arxiv_id(arxiv_id: str) -> str:
    """去掉版本号，统一为小写。"""
    s = arxiv_id.lower()
    # 去掉 v + 数字后缀
    if "v" in s:
        base, _, ver = s.rpartition("v")
        if ver.isdigit():
            return base
    return s


def extract_id_from_url(url: str) -> str:
    """从 arXiv URL 提取 ID（保留版本号）。"""
    m = ARXIV_URL_PATTERN.search(url)
    if not m:
        raise FetchError("arxiv_404", url=url)
    return m.group(1)
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```
Expected: 12 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/arxiv_fetch.py tests/unit/test_arxiv_fetch.py
git commit -m "feat(arxiv_fetch): add ID validation, normalization, URL extraction"
```

---

## Task 2.2: arxiv_fetch - 下载 PDF (mock 测试)

**Files:**
- Modify: `paper-intensive-reading/arxiv_fetch.py`
- Modify: `tests/unit/test_arxiv_fetch.py`

- [ ] **Step 1: 追加下载测试**

追加到 `tests/unit/test_arxiv_fetch.py`:
```python
class TestDownloadPdf:
    def test_download_to_path(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        class MockResult:
            entry_id = "http://arxiv.org/abs/2302.13971v1"
            title = "Test Paper"
            pdf_url = "http://arxiv.org/pdf/2302.13971v1"
            authors = [type("A", (), {"name": "Test Author"})()]
            summary = "Test abstract."
            published = date(2023, 2, 27)

            def download_pdf(self, dirpath, filename):
                Path(dirpath).mkdir(parents=True, exist_ok=True)
                Path(dirpath, filename).write_bytes(b"%PDF-1.4\n%fake\n")
                return str(Path(dirpath) / filename)

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([MockResult()])

        monkeypatch.setattr(arxiv_fetch.arxiv, "Client", MockClient)

        pdf_path = arxiv_fetch.fetch_by_arxiv_id("2302.13971", dest=tmp_workspace)
        assert pdf_path.exists()
        assert pdf_path.name == "2302.13971.pdf"
        assert pdf_path.stat().st_size > 0

    def test_invalid_id_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_arxiv_id("bad-id", dest=tmp_workspace)

    def test_cached_pdf_not_redownloaded(self, tmp_workspace):
        """已存在的 PDF 不重新下载"""
        from paper_intensive_reading import arxiv_fetch
        cached = tmp_workspace / "2302.13971.pdf"
        cached.write_bytes(b"%PDF-1.4\n%already cached\n")

        # 即使 arxiv 调用失败，缓存也应被返回
        pdf_path = arxiv_fetch.fetch_by_arxiv_id("2302.13971", dest=tmp_workspace)
        assert pdf_path == cached
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py::TestDownloadPdf -v
```

- [ ] **Step 3: 追加 fetch_by_arxiv_id**

追加到 `paper-intensive-reading/arxiv_fetch.py`:
```python
def fetch_by_arxiv_id(arxiv_id: str, dest: Path) -> Path:
    """根据 arXiv ID 下载 PDF。返回本地路径。"""
    validate_arxiv_id(arxiv_id)
    normalized = normalize_arxiv_id(arxiv_id)
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    target = dest / f"{normalized}.pdf"
    if target.exists() and target.stat().st_size > 1000:
        return target  # 已存在，跳过

    try:
        search = arxiv.Search(id_list=[arxiv_id])
        client = arxiv.Client(page_size=1, delay_seconds=3.0, num_retries=3)
        result = next(client.results(search))
        result.download_pdf(dirpath=str(dest), filename=f"{normalized}.pdf")
    except arxiv.ArticleNotFoundError as e:
        raise FetchError("arxiv_404", arxiv_id=arxiv_id) from e
    except arxiv.HTTPError as e:
        if getattr(e, "status", None) == 503:
            raise FetchError("arxiv_503", arxiv_id=arxiv_id) from e
        raise FetchError("arxiv_timeout", arxiv_id=arxiv_id) from e
    except Exception as e:
        raise FetchError("default", arxiv_id=arxiv_id, detail=str(e)) from e

    if not target.exists() or target.stat().st_size < 1000:
        raise FetchError("invalid_pdf", arxiv_id=arxiv_id)

    return target
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```
Expected: 15 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/arxiv_fetch.py tests/unit/test_arxiv_fetch.py
git commit -m "feat(arxiv_fetch): add fetch_by_arxiv_id with retry and cache"
```

---

## Task 2.3: arxiv_fetch - URL + 本地路径

**Files:**
- Modify: `paper-intensive-reading/arxiv_fetch.py`
- Modify: `tests/unit/test_arxiv_fetch.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_arxiv_fetch.py`:
```python
class TestFetchByUrl:
    def test_fetch_from_url(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target

        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        pdf_path = arxiv_fetch.fetch_by_url("https://arxiv.org/abs/2302.13971", dest=tmp_workspace)
        assert pdf_path.exists()
        assert pdf_path.name == "2302.13971.pdf"

    def test_non_arxiv_url_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_url("https://example.com/paper.pdf", dest=tmp_workspace)


class TestFetchByLocalPath:
    def test_valid_local_pdf(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        pdf = tmp_workspace / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%fake pdf content here\n")

        result = arxiv_fetch.fetch_by_local_path(str(pdf))
        assert result == pdf

    def test_nonexistent_path_raises(self):
        from paper_intensive_reading import arxiv_fetch
        with pytest.raises(FetchError) as exc:
            arxiv_fetch.fetch_by_local_path("/tmp/does-not-exist.pdf")
        assert exc.value.subtype == "arxiv_404"

    def test_non_pdf_file_raises(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        txt = tmp_workspace / "test.txt"
        txt.write_text("not a pdf")
        with pytest.raises(FetchError):
            arxiv_fetch.fetch_by_local_path(str(txt))

    def test_magic_byte_validation(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        pdf = tmp_workspace / "fake.pdf"
        pdf.write_bytes(b"NOT A PDF AT ALL")
        with pytest.raises(FetchError) as exc:
            arxiv_fetch.fetch_by_local_path(str(pdf))
        assert exc.value.subtype == "invalid_pdf"
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py::TestFetchByUrl tests/unit/test_arxiv_fetch.py::TestFetchByLocalPath -v
```

- [ ] **Step 3: 追加 fetch_by_url 和 fetch_by_local_path**

追加到 `paper-intensive-reading/arxiv_fetch.py`:
```python
def fetch_by_url(url: str, dest: Path) -> Path:
    """从 arXiv URL 下载 PDF。"""
    arxiv_id = extract_id_from_url(url)
    return fetch_by_arxiv_id(arxiv_id, dest=dest)


def fetch_by_local_path(path: str | Path) -> Path:
    """验证并返回本地 PDF 路径。"""
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FetchError("arxiv_404", path=str(p), detail="文件不存在")
    if p.suffix.lower() != ".pdf":
        raise FetchError("invalid_pdf", path=str(p), detail="扩展名不是 .pdf")
    with open(p, "rb") as f:
        head = f.read(8)
    if not head.startswith(b"%PDF-"):
        raise FetchError("invalid_pdf", path=str(p), detail="不是有效 PDF")
    return p
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```
Expected: 21 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/arxiv_fetch.py tests/unit/test_arxiv_fetch.py
git commit -m "feat(arxiv_fetch): add fetch_by_url and fetch_by_local_path"
```

---

## Task 2.4: arxiv_fetch - BibTeX 解析

**Files:**
- Modify: `paper-intensive-reading/arxiv_fetch.py`
- Modify: `tests/unit/test_arxiv_fetch.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_arxiv_fetch.py`:
```python
class TestFetchByBibtex:
    def test_parse_bibtex_with_eprint(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = """
@article{llama2023,
  title={LLaMA: Open and Efficient Foundation Language Models},
  author={Touvron and Lavril},
  year={2023},
  eprint={2302.13971},
  archivePrefix={arXiv}
}
"""
        arxiv_id = arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)
        assert arxiv_id == "2302.13971"

    def test_parse_bibtex_with_arxiv_url(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = """
@article{llama, title={LLaMA}, eprint={https://arxiv.org/abs/2302.13971}}
"""
        arxiv_id = arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)
        assert arxiv_id == "2302.13971"

    def test_parse_bibtex_no_id_raises(self):
        from paper_intensive_reading import arxiv_fetch
        bibtex = "@article{foo, title={No arxiv ID}}"
        with pytest.raises(FetchError):
            arxiv_fetch.extract_arxiv_id_from_bibtex(bibtex)

    def test_fetch_by_bibtex(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch
        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target
        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        bibtex = "@article{x, eprint={2302.13971}}"
        path = arxiv_fetch.fetch_by_bibtex(bibtex, dest=tmp_workspace)
        assert path.exists()
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py::TestFetchByBibtex -v
```

- [ ] **Step 3: 追加 BibTeX 解析**

追加到 `paper-intensive-reading/arxiv_fetch.py`:
```python
import bibtexparser


def extract_arxiv_id_from_bibtex(bibtex: str) -> str:
    """从 BibTeX 文本中提取 arXiv ID。"""
    try:
        db = bibtexparser.loads(bibtex)
        if not db.entries:
            raise FetchError("default", detail="BibTeX 无 entries")
        entry = db.entries[0]
        for field in ["eprint", "arxiv_id", "arxiv"]:
            if field in entry:
                value = entry[field]
                if "arxiv.org" in value:
                    return extract_id_from_url(value)
                return normalize_arxiv_id(value)
        raise FetchError("default", detail="BibTeX 不含 arXiv ID 字段")
    except FetchError:
        raise
    except Exception as e:
        raise FetchError("default", detail=f"解析 BibTeX 失败: {e}") from e


def fetch_by_bibtex(bibtex: str, dest: Path) -> Path:
    """从 BibTeX 提取 ID 后下载。"""
    arxiv_id = extract_arxiv_id_from_bibtex(bibtex)
    return fetch_by_arxiv_id(arxiv_id, dest=dest)
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```
Expected: 25 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/arxiv_fetch.py tests/unit/test_arxiv_fetch.py
git commit -m "feat(arxiv_fetch): add BibTeX parsing"
```

---

## Task 2.5: arxiv_fetch - 标题搜索 + 统一入口

**Files:**
- Modify: `paper-intensive-reading/arxiv_fetch.py`
- Modify: `tests/unit/test_arxiv_fetch.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_arxiv_fetch.py`:
```python
class TestFetchByTitle:
    def test_search_returns_results(self, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        class MockResult:
            entry_id = "http://arxiv.org/abs/2302.13971v1"
            title = "LLaMA: Open and Efficient Foundation Language Models"
            pdf_url = "http://arxiv.org/pdf/2302.13971v1"
            authors = [type("A", (), {"name": "Touvron"})()]
            summary = "We introduce LLaMA."
            published = date(2023, 2, 27)

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([MockResult()])

        monkeypatch.setattr(arxiv_fetch.arxiv, "Client", MockClient)

        papers = arxiv_fetch.search_arxiv("LLaMA", max_results=5)
        assert len(papers) == 1
        assert "LLaMA" in papers[0].title

    def test_no_results_raises(self, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([])

        monkeypatch.setattr(arxiv_fetch.arxiv, "Client", MockClient)

        with pytest.raises(FetchError) as exc:
            arxiv_fetch.search_arxiv("nonexistent paper xyz", max_results=5)
        assert exc.value.subtype == "arxiv_404"


class TestUnifiedFetch:
    def test_unified_fetch_with_arxiv_id(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch
        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target
        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        path = arxiv_fetch.fetch("2302.13971", dest=tmp_workspace)
        assert path.exists()

    def test_unified_fetch_with_url(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch
        def mock_fetch_by_id(arxiv_id, dest):
            target = dest / f"{arxiv_id}.pdf"
            target.write_bytes(b"%PDF-1.4\n%fake\n")
            return target
        monkeypatch.setattr(arxiv_fetch, "fetch_by_arxiv_id", mock_fetch_by_id)

        path = arxiv_fetch.fetch("https://arxiv.org/abs/2302.13971", dest=tmp_workspace)
        assert path.exists()

    def test_unified_fetch_with_local_path(self, tmp_workspace):
        from paper_intensive_reading import arxiv_fetch
        pdf = tmp_workspace / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%fake\n")
        path = arxiv_fetch.fetch(str(pdf), dest=tmp_workspace)
        assert path == pdf

    def test_unified_fetch_with_garbage_raises(self, tmp_workspace, monkeypatch):
        from paper_intensive_reading import arxiv_fetch

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([])

        monkeypatch.setattr(arxiv_fetch.arxiv, "Client", MockClient)

        with pytest.raises(FetchError):
            arxiv_fetch.fetch("totally garbage input that won't match", dest=tmp_workspace)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py::TestFetchByTitle tests/unit/test_arxiv_fetch.py::TestUnifiedFetch -v
```

- [ ] **Step 3: 追加 search_arxiv 和 fetch**

追加到 `paper-intensive-reading/arxiv_fetch.py`:
```python
def search_arxiv(query: str, max_results: int = 10) -> list[Paper]:
    """根据标题关键词搜索 arXiv。"""
    try:
        search = arxiv.Search(query=query, max_results=max_results,
                              sort_by=arxiv.SortCriterion.Relevance)
        client = arxiv.Client(page_size=max_results, delay_seconds=3.0, num_retries=3)
        results = list(client.results(search))
    except Exception as e:
        raise FetchError("arxiv_timeout", query=query, detail=str(e)) from e

    if not results:
        raise FetchError("arxiv_404", query=query, detail="搜索无结果")

    papers = []
    for r in results:
        arxiv_id = r.entry_id.split("/")[-1]
        arxiv_id = normalize_arxiv_id(arxiv_id)
        papers.append(Paper(
            arxiv_id=arxiv_id, title=r.title,
            authors=[a.name for a in r.authors], affiliations=[],
            abstract=r.summary,
            published=r.published.date() if r.published else date.today(),
            pdf_path="", sections=[], figures=[], tables=[],
            algorithms=[], references=[],
        ))
    return papers


def fetch(source: str, dest: Path) -> Path:
    """统一入口：自动识别 arXiv ID / URL / 本地路径 / BibTeX。"""
    s = source.strip()

    if s.startswith("@") or "eprint" in s:
        return fetch_by_bibtex(s, dest=dest)

    if s.startswith(("http://", "https://")):
        if "arxiv.org" in s:
            return fetch_by_url(s, dest=dest)
        raise FetchError("arxiv_404", url=s, detail="仅支持 arXiv URL")

    if s.startswith(("/", "./", "~")):
        return fetch_by_local_path(s)

    if "arxiv.org" in s:
        return fetch_by_url(s, dest=dest)

    if ARXIV_ID_PATTERN.match(s):
        return fetch_by_arxiv_id(s, dest=dest)

    # 标题搜索
    papers = search_arxiv(s, max_results=5)
    if not papers:
        raise FetchError("arxiv_404", query=s)
    return fetch_by_arxiv_id(papers[0].arxiv_id, dest=dest)
```

- [ ] **Step 4: 跑全部 arxiv_fetch 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_arxiv_fetch.py -v
```
Expected: ~30 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/arxiv_fetch.py tests/unit/test_arxiv_fetch.py
git commit -m "feat(arxiv_fetch): add title search and unified fetch() entry"
```

---

# 阶段 P3：论文解析 (pdf_parse)

## Task 3.1: pdf_parse - 安全检查 + 元数据

**Files:**
- Create: `paper-intensive-reading/pdf_parse.py`
- Test: `tests/unit/test_pdf_parse.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_pdf_parse.py`:
```python
import pytest
from pathlib import Path
from paper_intensive_reading.pdf_parse import check_pdf_safety, extract_metadata
from paper_intensive_reading.errors import ParseError


def _make_minimal_pdf(tmp_path: Path, with_js: bool = False) -> Path:
    if with_js:
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R /OpenAction 3 0 R>> endobj
2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj
3 0 obj <</S /JavaScript /JS (app.alert('hacked'))>> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000106 00000 n
trailer <</Size 4 /Root 1 0 R>> startxref 160 %%EOF
"""
    else:
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj
2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj
3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>> endobj
4 0 obj <</Length 44>> stream
BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET
endstream endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
0000000178 00000 n
trailer <</Size 5 /Root 1 0 R>> startxref 270 %%EOF
"""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(content)
    return pdf_path


class TestPdfSafety:
    def test_safe_pdf(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path, with_js=False)
        check_pdf_safety(pdf)

    def test_pdf_with_js_rejected(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path, with_js=True)
        with pytest.raises(ParseError) as exc:
            check_pdf_safety(pdf)
        assert exc.value.subtype == "dangerous"

    def test_nonexistent_raises(self, tmp_path):
        with pytest.raises(ParseError):
            check_pdf_safety(tmp_path / "missing.pdf")


class TestExtractMetadata:
    def test_basic_metadata(self, tmp_path):
        pdf = _make_minimal_pdf(tmp_path)
        meta = extract_metadata(pdf)
        assert "title" in meta
        assert "authors" in meta
        assert isinstance(meta["authors"], list)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py -v
```

- [ ] **Step 3: 写 pdf_parse.py 第一部分**

`paper-intensive-reading/pdf_parse.py`:
```python
"""PDF 解析：元数据、章节、公式、图表、表格、算法。"""
import re
from pathlib import Path
from datetime import date

import fitz  # PyMuPDF
import pikepdf

from .errors import ParseError
from .types import Paper, Section, Paragraph, Formula, Figure, Table, Algorithm, Reference


DANGEROUS_KEYS = {"/JS", "/JavaScript", "/AA", "/OpenAction", "/Launch", "/URI", "/SubmitForm"}


def check_pdf_safety(pdf_path: Path) -> None:
    """检查 PDF 是否安全。危险时抛 ParseError。"""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise ParseError("default", path=str(pdf_path), detail="文件不存在")
    try:
        with pikepdf.open(pdf_path) as pdf:
            if pdf.is_encrypted:
                raise ParseError("encrypted", path=str(pdf_path))
            for obj in pdf.objects:
                obj_str = str(obj)
                for key in DANGEROUS_KEYS:
                    if key in obj_str:
                        raise ParseError("dangerous", path=str(pdf_path), detail=f"发现 {key}")
    except pikepdf.PasswordError as e:
        raise ParseError("encrypted", path=str(pdf_path)) from e
    except ParseError:
        raise
    except Exception as e:
        raise ParseError("default", path=str(pdf_path), detail=str(e)) from e


def extract_metadata(pdf_path: Path) -> dict:
    """提取 PDF 元数据。"""
    pdf_path = Path(pdf_path)
    metadata: dict = {
        "title": "", "authors": [], "abstract": "", "published": date.today(),
    }
    with fitz.open(pdf_path) as doc:
        info = doc.metadata or {}
        metadata["title"] = (info.get("title") or "").strip()
        metadata["authors"] = [a.strip() for a in (info.get("author") or "").split(",") if a.strip()]
        if not metadata["title"] and doc.page_count > 0:
            first_text = doc[0].get_text()
            lines = [l.strip() for l in first_text.split("\n") if l.strip()]
            if lines:
                metadata["title"] = lines[0][:200]
    return metadata
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/pdf_parse.py tests/unit/test_pdf_parse.py
git commit -m "feat(pdf_parse): add safety check and metadata extraction"
```

---

## Task 3.2: pdf_parse - 章节识别

**Files:**
- Modify: `paper-intensive-reading/pdf_parse.py`
- Modify: `tests/unit/test_pdf_parse.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_pdf_parse.py`:
```python
class TestExtractSections:
    def test_recognizes_standard_sections(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_sections
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        for page_text in [
            "Title\n\nAbstract content here.",
            "1 Introduction\n\nThis is the intro.",
            "2 Method\n\nOur method is great.",
            "2.1 Submethod\n\nDetails.",
            "3 Experiments\n\nResults are good.",
        ]:
            page = doc.new_page()
            page.insert_text((50, 50), page_text)
        doc.save(str(pdf))
        doc.close()

        sections = extract_sections(pdf)
        titles = [s.title for s in sections]
        assert any("Introduction" in t for t in titles)
        assert any("Method" in t for t in titles)
        assert any("Experiments" in t for t in titles)

    def test_section_numbers(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_sections
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((50, 50), "1 Introduction\n\nBody")
        doc.new_page().insert_text((50, 50), "2.1 Sub\n\nBody")
        doc.save(str(pdf))
        doc.close()

        sections = extract_sections(pdf)
        assert any(s.number == "1" for s in sections)
        assert any(s.number == "2.1" for s in sections)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py::TestExtractSections -v
```

- [ ] **Step 3: 追加 extract_sections**

追加到 `paper-intensive-reading/pdf_parse.py`:
```python
SECTION_PATTERN = re.compile(
    r"^(\d+(?:\.\d+)*)\s+([A-Z][A-Za-z][A-Za-z0-9 \-:_&/]{1,80})$",
    re.MULTILINE,
)


def _looks_like_section_title(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or len(line) > 100:
        return None
    m = SECTION_PATTERN.match(line)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def extract_sections(pdf_path: Path) -> list[Section]:
    """从 PDF 提取章节结构。"""
    pdf_path = Path(pdf_path)
    sections: list[Section] = []
    current: Section | None = None
    body_lines: list[str] = []

    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for line in text.split("\n"):
                parsed = _looks_like_section_title(line)
                if parsed is not None:
                    if current is not None:
                        current.paragraphs.append(
                            Paragraph(text="\n".join(body_lines).strip(), page=page_idx)
                        )
                        sections.append(current)
                    number, title = parsed
                    level = number.count(".") + 1
                    current = Section(number=number, title=title, level=level)
                    body_lines = []
                else:
                    if current is not None:
                        body_lines.append(line)

        if current is not None:
            current.paragraphs.append(
                Paragraph(text="\n".join(body_lines).strip(), page=doc.page_count - 1)
            )
            sections.append(current)

    if not sections:
        raise ParseError("no_sections", path=str(pdf_path))
    return sections
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py -v
```
Expected: 6 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/pdf_parse.py tests/unit/test_pdf_parse.py
git commit -m "feat(pdf_parse): add section recognition"
```

---

## Task 3.3: pdf_parse - 公式/图表/表格/算法

**Files:**
- Modify: `paper-intensive-reading/pdf_parse.py`
- Modify: `tests/unit/test_pdf_parse.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_pdf_parse.py`:
```python
class TestExtractFormulas:
    def test_extract_formula_numbers(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_formulas
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "We define Loss = -sum(y * log(p)) in Eq. (1).\n"
            "The attention is QK^T / sqrt(d) in equation (2).",
        )
        doc.save(str(pdf))
        doc.close()

        formulas = extract_formulas(pdf)
        assert any(f.number == "(1)" for f in formulas)
        assert any(f.number == "(2)" for f in formulas)

    def test_no_formulas_returns_empty(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_formulas
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text((50, 50), "Plain text without formulas.")
        doc.save(str(pdf))
        doc.close()

        assert extract_formulas(pdf) == []


class TestExtractFiguresTablesAlgorithms:
    def test_figure_captions(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_figure_captions
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Some text.\n\nFigure 1: Overview of our model architecture.\n\n"
            "Figure 2: Training loss curves over 100 epochs.",
        )
        doc.save(str(pdf))
        doc.close()

        captions = extract_figure_captions(pdf)
        assert len(captions) == 2
        assert "Overview" in captions[0]["caption"]

    def test_table_captions(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_tables
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Table 1: Main results on ImageNet.\nTable 2: Ablation study.",
        )
        doc.save(str(pdf))
        doc.close()

        tables = extract_tables(pdf)
        assert len(tables) == 2

    def test_algorithm_blocks(self, tmp_path):
        from paper_intensive_reading.pdf_parse import extract_algorithms
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Algorithm 1: Training procedure\n"
            "1: Initialize model\n2: for epoch in range(N):\n3:    train()\n4: end for",
        )
        doc.save(str(pdf))
        doc.close()

        algos = extract_algorithms(pdf)
        assert len(algos) == 1
        assert "Training" in algos[0].title
        assert "Initialize" in algos[0].pseudocode
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py::TestExtractFormulas tests/unit/test_pdf_parse.py::TestExtractFiguresTablesAlgorithms -v
```

- [ ] **Step 3: 追加提取函数**

追加到 `paper-intensive-reading/pdf_parse.py`:
```python
FORMULA_NUM_PATTERN = re.compile(
    r"\(?\b(?:Eq\.?|equation|formula|式)\s*\(?(\d+(?:\.\d+)?)\)?",
    re.IGNORECASE,
)
FIGURE_PATTERN = re.compile(
    r"Figure\s+(\d+)\s*[:.]\s*(.+?)(?=\n\s*(?:Figure|Table|\d+\.|\Z))",
    re.DOTALL,
)
TABLE_PATTERN = re.compile(
    r"Table\s+(\d+)\s*[:.]\s*(.+?)(?=\n\s*(?:Figure|Table|\d+\.|\Z))",
    re.DOTALL,
)
ALGORITHM_PATTERN = re.compile(r"Algorithm\s+(\d+)\s*[:.]\s*([^\n]+)")


def extract_formulas(pdf_path: Path) -> list[Formula]:
    """从 PDF 文本中提取公式编号（不 OCR 公式本身）。"""
    pdf_path = Path(pdf_path)
    formulas: list[Formula] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in FORMULA_NUM_PATTERN.finditer(text):
                number = f"({m.group(1)})"
                formulas.append(Formula(
                    number=number, latex="",
                    context_before=text[max(0, m.start() - 200):m.start()].strip(),
                    context_after=text[m.end():min(len(text), m.end() + 200)].strip(),
                    symbols={},
                ))
    # 去重
    seen: set[str] = set()
    unique = []
    for f in formulas:
        if f.number not in seen:
            seen.add(f.number)
            unique.append(f)
    return unique


def extract_figure_captions(pdf_path: Path) -> list[dict]:
    pdf_path = Path(pdf_path)
    captions: list[dict] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in FIGURE_PATTERN.finditer(text):
                captions.append({
                    "number": f"Figure {m.group(1)}",
                    "caption": m.group(2).strip()[:500],
                    "page": page_idx,
                })
    return captions


def extract_tables(pdf_path: Path) -> list[Table]:
    pdf_path = Path(pdf_path)
    tables: list[Table] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in TABLE_PATTERN.finditer(text):
                tables.append(Table(
                    number=f"Table {m.group(1)}",
                    caption=m.group(2).strip()[:500],
                    headers=[], rows=[],
                ))
    return tables


def extract_algorithms(pdf_path: Path) -> list[Algorithm]:
    pdf_path = Path(pdf_path)
    algos: list[Algorithm] = []
    with fitz.open(pdf_path) as doc:
        for page_idx in range(doc.page_count):
            text = doc[page_idx].get_text()
            for m in ALGORITHM_PATTERN.finditer(text):
                title = m.group(2).strip()
                start = m.end()
                lines = text[start:].split("\n")[:20]
                pseudocode = "\n".join(lines).strip()
                algos.append(Algorithm(
                    number=f"Algorithm {m.group(1)}",
                    title=title, pseudocode=pseudocode,
                    language_hint="pseudocode",
                ))
    return algos
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py -v
```
Expected: 10 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/pdf_parse.py tests/unit/test_pdf_parse.py
git commit -m "feat(pdf_parse): add formula/figure/table/algorithm extraction"
```

---

## Task 3.4: pdf_parse - 统一 parse() 入口

**Files:**
- Modify: `paper-intensive-reading/pdf_parse.py`
- Modify: `tests/unit/test_pdf_parse.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_pdf_parse.py`:
```python
class TestUnifiedParse:
    def test_parse_returns_paper(self, tmp_path):
        from paper_intensive_reading.pdf_parse import parse
        import fitz

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        doc.new_page().insert_text(
            (50, 50),
            "Test Paper Title\n\nAbstract: We propose something.\n\n"
            "1 Introduction\n\nIntro text.\n\n"
            "2 Method\n\nEq. (1): x = y + z.\n\n"
            "Figure 1: Architecture diagram.",
        )
        doc.save(str(pdf))
        doc.close()

        paper = parse(pdf)
        assert "Test Paper" in paper.title
        assert len(paper.sections) >= 2
        assert paper.pdf_path == str(pdf)

    def test_parse_unsafe_pdf_raises(self, tmp_path):
        from paper_intensive_reading.pdf_parse import parse
        content = b"""%PDF-1.4
1 0 obj <</Type /Catalog /Pages 2 0 R /OpenAction 3 0 R>> endobj
2 0 obj <</Type /Pages /Kids [] /Count 0>> endobj
3 0 obj <</S /JavaScript /JS (alert(1))>> endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000106 00000 n
trailer <</Size 4 /Root 1 0 R>> startxref 160 %%EOF
"""
        pdf = tmp_path / "evil.pdf"
        pdf.write_bytes(content)

        with pytest.raises(ParseError):
            parse(pdf)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py::TestUnifiedParse -v
```

- [ ] **Step 3: 追加 parse()**

追加到 `paper-intensive-reading/pdf_parse.py`:
```python
def parse(pdf_path: str | Path) -> Paper:
    """解析 PDF 为 Paper 对象。统一入口。"""
    pdf_path = Path(pdf_path)

    check_pdf_safety(pdf_path)
    meta = extract_metadata(pdf_path)
    sections = extract_sections(pdf_path)
    formulas = extract_formulas(pdf_path)
    figures_meta = extract_figure_captions(pdf_path)
    tables = extract_tables(pdf_path)
    algorithms = extract_algorithms(pdf_path)

    # 公式归入对应章节
    for f in formulas:
        for sec in sections:
            if any(f.number in p.text for p in sec.paragraphs):
                sec.formulas.append(f)
                break

    # Figure 对象
    figures = [
        Figure(
            number=fig["number"], caption=fig["caption"],
            image_path="", page=fig["page"],
        )
        for fig in figures_meta
    ]

    abstract = meta.get("abstract", "")
    if not abstract and sections:
        for sec in sections:
            if "abstract" in sec.title.lower():
                abstract = "\n".join(p.text for p in sec.paragraphs)
                break

    return Paper(
        arxiv_id="",
        title=meta.get("title", ""),
        authors=meta.get("authors", []),
        affiliations=meta.get("affiliations", []),
        abstract=abstract,
        published=meta.get("published") or date.today(),
        pdf_path=str(pdf_path),
        sections=sections, figures=figures, tables=tables,
        algorithms=algorithms, references=[],
    )
```

- [ ] **Step 4: 跑全部 pdf_parse 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_pdf_parse.py -v
```
Expected: 12 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/pdf_parse.py tests/unit/test_pdf_parse.py
git commit -m "feat(pdf_parse): add unified parse() entry"
```

---

# 阶段 P4：图表提取 (extract_figures)

## Task 4.1: extract_figures - 抠图 + 页渲染

**Files:**
- Create: `paper-intensive-reading/extract_figures.py`
- Test: `tests/unit/test_extract_figures.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_extract_figures.py`:
```python
import pytest
from pathlib import Path
from paper_intensive_reading.extract_figures import (
    extract_embedded_images, render_page_region
)


def test_extract_embedded_images(tmp_path):
    import fitz
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page()
    img = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    img.clear_with(255)
    page.insert_image(fitz.Rect(50, 50, 200, 200), pixmap=img)
    doc.save(str(pdf))
    doc.close()

    out_dir = tmp_path / "figs"
    paths = extract_embedded_images(pdf, out_dir)
    assert len(paths) >= 1
    assert all(Path(p).exists() for p in paths)


def test_render_page_region(tmp_path):
    import fitz
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "Test page content")
    doc.save(str(pdf))
    doc.close()

    out = tmp_path / "page.png"
    render_page_region(pdf, page_num=0, out_path=out)
    assert out.exists()
    assert out.stat().st_size > 0
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_extract_figures.py -v
```

- [ ] **Step 3: 写 extract_figures.py**

`paper-intensive-reading/extract_figures.py`:
```python
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_extract_figures.py -v
```
Expected: 2 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/extract_figures.py tests/unit/test_extract_figures.py
git commit -m "feat(extract_figures): add embedded image extraction and page rendering"
```

---

## Task 4.2: extract_figures - 整合到 Figure 列表

**Files:**
- Modify: `paper-intensive-reading/extract_figures.py`
- Modify: `tests/unit/test_extract_figures.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_extract_figures.py`:
```python
class TestAttachFigures:
    def test_attach_images_to_figures(self, tmp_path):
        import fitz
        from paper_intensive_reading.extract_figures import attach_images_to_figures
        from paper_intensive_reading.types import Figure

        pdf = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        img = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 50, 50), False)
        img.clear_with(200)
        page.insert_image(fitz.Rect(100, 100, 200, 200), pixmap=img)
        doc.save(str(pdf))
        doc.close()

        figures = [Figure(number="Figure 1", caption="Test", image_path="", page=0)]
        out_dir = tmp_path / "figs"
        attach_images_to_figures(pdf, figures, out_dir)

        assert any(f.image_path for f in figures)
        assert any(Path(f.image_path).exists() for f in figures if f.image_path)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_extract_figures.py::TestAttachFigures -v
```

- [ ] **Step 3: 追加 attach_images_to_figures**

追加到 `paper-intensive-reading/extract_figures.py`:
```python
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_extract_figures.py -v
```
Expected: 3 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/extract_figures.py tests/unit/test_extract_figures.py
git commit -m "feat(extract_figures): add attach_images_to_figures"
```

---

# 阶段 P5：公式渲染 (render_formula)

## Task 5.1: render_formula - 基础 LaTeX → PNG

**Files:**
- Create: `paper-intensive-reading/render_formula.py`
- Test: `tests/unit/test_render_formula.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_render_formula.py`:
```python
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
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_render_formula.py -v
```

- [ ] **Step 3: 写 render_formula.py**

`paper-intensive-reading/render_formula.py`:
```python
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_render_formula.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/render_formula.py tests/unit/test_render_formula.py
git commit -m "feat(render_formula): add LaTeX-to-PNG via matplotlib mathtext"
```

---

## Task 5.2: render_formula - 批量渲染

**Files:**
- Modify: `paper-intensive-reading/render_formula.py`
- Modify: `tests/unit/test_render_formula.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_render_formula.py`:
```python
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
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_render_formula.py::TestBatchRender -v
```

- [ ] **Step 3: 追加 render_batch**

追加到 `paper-intensive-reading/render_formula.py`:
```python
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_render_formula.py -v
```
Expected: 6 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/render_formula.py tests/unit/test_render_formula.py
git commit -m "feat(render_formula): add batch rendering with skip-failures"
```

---

# 阶段 P6：NumPy 沙箱 (numpy_runner)

## Task 6.1: numpy_runner - 静态白名单检查

**Files:**
- Create: `paper-intensive-reading/numpy_runner.py`
- Test: `tests/unit/test_numpy_runner.py`
- Test: `tests/safety/test_safety.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_numpy_runner.py`:
```python
import pytest
from paper_intensive_reading.numpy_runner import (
    validate_imports, validate_names, parse_code_safety
)
from paper_intensive_reading.errors import NumPyRunError


class TestValidateImports:
    def test_numpy_allowed(self):
        validate_imports("import numpy as np\nx = np.array([1,2,3])")

    def test_numpy_bare_allowed(self):
        validate_imports("import numpy\nx = numpy.array([1,2,3])")

    def test_os_blocked(self):
        with pytest.raises(NumPyRunError) as exc:
            validate_imports("import os")
        assert exc.value.subtype == "forbidden_import"

    def test_subprocess_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import subprocess")

    def test_requests_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import requests")

    def test_urllib_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("from urllib.request import urlopen")

    def test_sys_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import sys")


class TestValidateNames:
    def test_safe_names(self):
        validate_names("x = 1\ny = x + 2")

    def test_open_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("open('/etc/passwd')")

    def test_exec_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("exec('print(1)')")

    def test_eval_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("eval('1+1')")

    def test_getattr_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("getattr(np, 'array')")

    def test_globals_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("globals()['__builtins__']")

    def test_dunder_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("x.__class__.__bases__")


class TestParseCodeSafety:
    def test_safe_code_passes(self):
        parse_code_safety("import numpy as np\nx = np.array([1,2,3])")

    def test_combined_violations(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import os\nopen('/etc/passwd')")

    def test_syntax_error_caught(self):
        with pytest.raises(NumPyRunError) as exc:
            parse_code_safety("import numpy as np\nx = (1,2,3")
        assert exc.value.subtype == "syntax"
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_numpy_runner.py -v
```

- [ ] **Step 3: 写 numpy_runner.py 第一部分**

`paper-intensive-reading/numpy_runner.py`:
```python
"""安全执行用户提供的 NumPy 代码。"""
import ast
from .errors import NumPyRunError

ALLOWED_IMPORTS = {"numpy", "numpy as np"}
FORBIDDEN_NAMES = {
    "os", "sys", "subprocess", "shutil", "pathlib", "glob",
    "open", "exec", "eval", "compile", "input",
    "socket", "urllib", "requests", "http", "ftplib", "smtplib",
    "ctypes", "cffi", "multiprocessing", "threading",
    "__import__", "getattr", "globals", "locals", "vars", "dir",
    "breakpoint", "memoryview",
}
FORBIDDEN_ATTRS = {
    "__class__", "__bases__", "__subclasses__", "__globals__",
    "__code__", "__dict__", "__module__", "__import__",
}


def validate_imports(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod != "numpy":
                    raise NumPyRunError("forbidden_import", detail=f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod != "numpy":
                raise NumPyRunError("forbidden_import", detail=f"from {node.module} import ...")


def validate_names(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise NumPyRunError("forbidden_name", detail=f"name '{node.id}'")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            raise NumPyRunError("forbidden_name", detail=f"attribute '{node.attr}'")


def parse_code_safety(code: str) -> ast.Module:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise NumPyRunError("syntax", detail=str(e)) from e
    validate_imports(code)
    validate_names(code)
    return tree
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_numpy_runner.py -v
```
Expected: 17 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/numpy_runner.py tests/unit/test_numpy_runner.py
git commit -m "feat(numpy_runner): add static safety checks"
```

---

## Task 6.2: numpy_runner - 子进程隔离执行

**Files:**
- Modify: `paper-intensive-reading/numpy_runner.py`
- Modify: `tests/unit/test_numpy_runner.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_numpy_runner.py`:
```python
class TestRunCode:
    def test_simple_execution(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import numpy as np\nx = np.array([1, 2, 3])\nprint(x.sum())"
        result = run(code)
        assert result.ok
        assert "6" in result.stdout

    def test_timeout(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import time\ntime.sleep(15)"
        result = run(code, timeout=2)
        assert not result.ok
        assert result.error_subtype == "timeout"

    def test_runtime_error(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import numpy as np\nx = np.array([1, 2])\nprint(x[10])"
        result = run(code)
        assert not result.ok
        assert "IndexError" in result.stderr

    def test_syntax_error_caught(self):
        from paper_intensive_reading.numpy_runner import run
        code = "x = (1, 2,"
        result = run(code)
        assert not result.ok
        assert result.error_subtype == "syntax"

    def test_output_truncation(self):
        from paper_intensive_reading.numpy_runner import run
        code = "print('x' * 20000)"
        result = run(code, max_output=1024)
        assert result.ok
        assert len(result.stdout) <= 2048
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_numpy_runner.py::TestRunCode -v
```

- [ ] **Step 3: 追加 run()**

追加到 `paper-intensive-reading/numpy_runner.py`:
```python
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass


@dataclass
class RunResult:
    ok: bool
    stdout: str
    stderr: str
    duration_s: float
    error_subtype: str = ""
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok, "stdout": self.stdout, "stderr": self.stderr,
            "duration_s": self.duration_s, "error_subtype": self.error_subtype,
            "error_message": self.error_message,
        }


_RUNNER_TEMPLATE = """
import sys
import resource
resource.setrlimit(resource.RLIMIT_AS, ({memory_mb} * 1024 * 1024, {memory_mb} * 1024 * 1024))
import numpy as np
try:
{code}
except Exception as e:
    print(f"__ERROR__{{type(e).__name__}}: {{e}}", file=sys.stderr)
    sys.exit(1)
"""


def run(
    code: str, timeout: int = 10, memory_mb: int = 256, max_output: int = 10240,
) -> RunResult:
    """在子进程中安全执行 NumPy 代码。"""
    try:
        parse_code_safety(code)
    except NumPyRunError as e:
        return RunResult(ok=False, stdout="", stderr="", duration_s=0.0,
                         error_subtype=e.subtype, error_message=str(e.context.get("detail", "")))

    indented = "\n".join("    " + line for line in code.split("\n"))
    runner_src = _RUNNER_TEMPLATE.format(code=indented, memory_mb=memory_mb)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(runner_src)
        tmp_path = f.name

    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, tmp_path], capture_output=True, text=True,
            timeout=timeout, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": ""},
        )
        duration = time.time() - start
        stdout = proc.stdout[:max_output]
        stderr = proc.stderr[:max_output]

        if proc.returncode == 0:
            return RunResult(ok=True, stdout=stdout, stderr=stderr, duration_s=duration)

        if "SyntaxError" in stderr:
            subtype = "syntax"
        elif "MemoryError" in stderr:
            subtype = "memory"
        else:
            subtype = "runtime"
        return RunResult(ok=False, stdout=stdout, stderr=stderr, duration_s=duration,
                         error_subtype=subtype, error_message=stderr[:500])
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return RunResult(ok=False, stdout="", stderr="", duration_s=duration,
                         error_subtype="timeout", error_message=f"超过 {timeout} 秒")
    finally:
        try:
            from pathlib import Path
            Path(tmp_path).unlink()
        except Exception:
            pass
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_numpy_runner.py -v
```
Expected: 22 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/numpy_runner.py tests/unit/test_numpy_runner.py
git commit -m "feat(numpy_runner): add subprocess-isolated execution with timeout and memory"
```

---

## Task 6.3: numpy_runner - 沙箱绕过测试

**Files:**
- Create: `tests/safety/test_safety.py`

- [ ] **Step 1: 写测试**

`tests/safety/test_safety.py`:
```python
"""沙箱绕过测试：确保 numpy_runner 不能执行危险操作。"""
import pytest
from paper_intensive_reading.numpy_runner import run, parse_code_safety
from paper_intensive_reading.errors import NumPyRunError


class TestSandboxBypass:
    def test_os_system_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import os\nos.system('whoami')")

    def test_subprocess_run_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import subprocess\nsubprocess.run(['ls'])")

    def test_open_file_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("open('/etc/passwd').read()")

    def test_dunder_traversal_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("x = ().__class__.__bases__[0].__subclasses__()")

    def test_eval_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("eval('1+1')")

    def test_exec_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("exec('import os')")

    def test_getattr_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("getattr(__builtins__, 'open')")

    def test_socket_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import socket")

    def test_urllib_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("from urllib.request import urlopen")

    def test_pickle_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import pickle")

    def test_ctypes_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import ctypes")


class TestRealisticUse:
    def test_attention_calculation(self):
        code = """
import numpy as np
Q = np.array([[1, 0, 1, 0]])
K = np.array([[1, 1, 0, 0]])
V = np.array([[0.5, 0.5]])
scores = Q @ K.T / np.sqrt(4)
def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()
weights = softmax(scores)
output = weights @ V
print(f"scores: {scores}")
print(f"weights: {weights}")
print(f"output: {output}")
"""
        result = run(code)
        assert result.ok
        assert "scores:" in result.stdout
        assert "output:" in result.stdout

    def test_matrix_multiplication(self):
        code = """
import numpy as np
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
print(A @ B)
"""
        result = run(code)
        assert result.ok
        assert "19" in result.stdout
```

- [ ] **Step 2: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/safety/test_safety.py -v
```
Expected: 13 tests pass

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add tests/safety/test_safety.py
git commit -m "test(safety): add sandbox bypass tests for numpy_runner"
```

---

## Task 6.4: numpy_runner - 真实 Attention 集成测试

**Files:**
- Create: `tests/integration/test_numpy_runner_attention.py`

- [ ] **Step 1: 写测试**

`tests/integration/test_numpy_runner_attention.py`:
```python
"""集成测试：跑完整的 Attention 三对照例子。"""
import pytest
from paper_intensive_reading.numpy_runner import run


@pytest.mark.integration
def test_attention_three_way_verification():
    code = """
import numpy as np
d_k = 4
Q = np.array([[1, 0, 1, 0],
              [0, 1, 0, 1],
              [1, 1, 0, 0]])
K = np.array([[1, 1, 0, 0],
              [0, 1, 1, 0],
              [1, 0, 0, 1]])
V = np.array([[0.5, 0.5],
              [0.8, 0.2],
              [0.3, 0.7]])
scores = Q @ K.T
print(f"Step 1 (QK^T) =\\n{scores}")
scores = scores / np.sqrt(d_k)
print(f"Step 2 (/sqrt({d_k})) =\\n{scores}")
def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
weights = softmax(scores)
print(f"Step 3 (softmax) =\\n{weights}")
output = weights @ V
print(f"Step 4 (×V) =\\n{output}")
"""
    result = run(code, timeout=10)
    assert result.ok, f"代码运行失败: {result.error_message}"
    assert "Step 1" in result.stdout
    assert "Step 4" in result.stdout
```

- [ ] **Step 2: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/integration/test_numpy_runner_attention.py -v
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add tests/integration/test_numpy_runner_attention.py
git commit -m "test(integration): verify Attention calculation runs end-to-end"
```

---

# 阶段 P7：概念阶梯 + 术语

## Task 7.1: math-ladder.md 概念阶梯文档

**Files:**
- Create: `references/math-ladder.md`

- [ ] **Step 1: 写概念阶梯**

`references/math-ladder.md`:
```markdown
# 数学概念阶梯

> 给 AI 用的"用户数学基础"参考表。预设用户只有小学数学。
> 讲公式时按这个阶梯决定从哪层开始讲。

## 第 0 层：算术（默认起点）
- 加减乘除、分数、小数、百分数
- 例：把 100 个苹果分给 4 个人 → 平均数 25

## 第 1 层：基本代数
- 用字母代替数字：a + b = b + a
- 未知数：x + 3 = 5 → x = 2
- **比喻**：x 是"还不知道的数"，我们要把它找出来

## 第 2 层：函数与图像
- 函数 f(x) = 2x：输入 x，输出两倍
- **比喻**：函数是一台"机器"，左边进右边出

## 第 3 层：指数和对数
- 指数：2^3 = 8 → "翻倍几次"
- 对数：log₂(8) = 3 → "8 是怎么变来的？翻了 3 次"
- **比喻**：指数是"火箭发射"，对数是"倒带看发射过程"

## 第 4 层：概率与统计
- 概率：扔硬币正面朝上的可能性是 1/2
- 平均数、方差
- **比喻**：方差就是"大家离平均有多远"

## 第 5 层：向量与矩阵（LLM 必备）
- 向量：一列数字 [1, 2, 3] → 三个属性的"打包"
- 矩阵：很多向量排成表格
- 矩阵乘法：变换 / 投影 / 组合
- **比喻**：向量是"购物清单"，矩阵是"商品价格表"，乘法是"算总价"

## 第 6 层：导数与梯度
- 导数：函数"变化的速度"
- **比喻**：开车时速度表显示的就是导数
- 梯度：多元函数的"方向导数"

## 第 7 层：注意力机制的数学
- Q/K/V：用"查字典"比喻
- Softmax：把分数变成百分比
- Attention：每个词去"查其他词的字典"

## 公式 → 阶梯层映射

| 公式 / 概念 | 起始层 |
|------------|--------|
| x + y = z | 0 |
| f(x) = 2x | 2 |
| a^x | 3 |
| log(x) | 3 |
| mean, var | 4 |
| softmax | 4 |
| vector, matrix | 5 |
| matrix multiply | 5 |
| Q·K, QK^T | 5 |
| derivative | 6 |
| gradient | 6 |
| Attention | 7 |
| RMSNorm | 5+ |
| SwiGLU | 5+ |
| RoPE | 5+7 |
```

- [ ] **Step 2: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add references/math-ladder.md
git commit -m "docs(math_ladder): add 8-layer concept ladder reference"
```

---

## Task 7.2: math_ladder.py 实现

**Files:**
- Create: `paper-intensive-reading/math_ladder.py`
- Test: `tests/unit/test_math_ladder.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_math_ladder.py`:
```python
import pytest
from paper_intensive_reading.math_ladder import (
    path_for, layers_for_concept, describe_layer, ALL_LAYERS
)


class TestPathFor:
    def test_softmax_needs_probability(self):
        assert 4 in path_for("softmax")

    def test_attention_needs_matrix_and_probability(self):
        layers = path_for("attention")
        assert 5 in layers
        assert 4 in layers

    def test_simple_arithmetic(self):
        assert 0 in path_for("x + y")

    def test_rmsnorm_needs_matrix(self):
        assert 5 in path_for("rmsnorm")

    def test_unknown_concept_returns_layer_0(self):
        assert path_for("totally-unknown-xyz") == [0]

    def test_layer_order_ascending(self):
        layers = path_for("attention")
        assert layers == sorted(layers)


class TestLayersForConcept:
    def test_known_concept(self):
        assert 5 in layers_for_concept("matrix multiply")

    def test_case_insensitive(self):
        assert 4 in layers_for_concept("SoftMax")

    def test_strip_whitespace(self):
        assert 4 in layers_for_concept("  softmax  ")


class TestDescribeLayer:
    def test_describe_layer_0(self):
        desc = describe_layer(0)
        assert "算术" in desc or "加减" in desc

    def test_describe_layer_5(self):
        desc = describe_layer(5)
        assert "向量" in desc or "矩阵" in desc

    def test_invalid_layer(self):
        with pytest.raises(ValueError):
            describe_layer(99)


def test_all_layers_defined():
    assert len(ALL_LAYERS) == 8
    assert all(i in ALL_LAYERS for i in range(8))
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_math_ladder.py -v
```

- [ ] **Step 3: 写 math_ladder.py**

`paper-intensive-reading/math_ladder.py`:
```python
"""数学概念阶梯：决定讲公式时从哪层开始。"""

_CONCEPT_TO_LAYER: dict[str, int] = {
    "+": 0, "-": 0, "*": 0, "/": 0, "sum": 0, "average": 0, "min": 0, "max": 0,
    "x + y": 1, "x = 1": 1, "variable": 1, "unknown": 1,
    "f(x)": 2, "function": 2, "graph": 2,
    "exp": 3, "log": 3, "logarithm": 3, "exponential": 3, "power": 3,
    "probability": 4, "softmax": 4, "mean": 4, "variance": 4, "distribution": 4,
    "cross-entropy": 4,
    "vector": 5, "matrix": 5, "matrix multiply": 5, "matmul": 5,
    "dot product": 5, "QK": 5, "QK^T": 5, "Q·K": 5,
    "embedding": 5, "linear layer": 5,
    "rmsnorm": 5, "layernorm": 5, "batchnorm": 5, "normalization": 5,
    "gelu": 5, "relu": 5, "sigmoid": 5, "tanh": 5,
    "swiglu": 5,
    "derivative": 6, "gradient": 6, "chain rule": 6, "backpropagation": 6,
    "attention": 7, "self-attention": 7, "cross-attention": 7,
    "rope": 7, "qkv": 7, "Q": 7, "K": 7, "V": 7,
    "multi-head": 7, "transformer": 7,
}

LAYER_DESCRIPTIONS: dict[int, str] = {
    0: "第 0 层：算术（加减乘除、分数、小数、百分数）",
    1: "第 1 层：基本代数（用字母代替数字、未知数）",
    2: "第 2 层：函数与图像（输入输出、坐标）",
    3: "第 3 层：指数和对数（翻倍、对应的反向）",
    4: "第 4 层：概率与统计（可能性、平均数、方差）",
    5: "第 5 层：向量与矩阵（一列数、表格、乘法）",
    6: "第 6 层：导数与梯度（变化速度、最陡方向）",
    7: "第 7 层：注意力机制（Q/K/V、查字典）",
}

ALL_LAYERS = list(range(8))


def layers_for_concept(concept: str) -> list[int]:
    concept = concept.strip().lower()
    layer = _CONCEPT_TO_LAYER.get(concept)
    if layer is None:
        return [0]
    return [layer]


def path_for(topic: str) -> list[int]:
    layers = layers_for_concept(topic)
    max_layer = max(layers)
    return list(range(max_layer + 1))


def describe_layer(layer: int) -> str:
    if layer not in LAYER_DESCRIPTIONS:
        raise ValueError(f"层 {layer} 不存在（0-7）")
    return LAYER_DESCRIPTIONS[layer]
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_math_ladder.py -v
```
Expected: 14 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/math_ladder.py tests/unit/test_math_ladder.py
git commit -m "feat(math_ladder): add concept-to-layer mapping"
```

---

## Task 7.3: bilingual.py 术语映射

**Files:**
- Create: `paper-intensive-reading/bilingual.py`
- Test: `tests/unit/test_bilingual.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_bilingual.py`:
```python
import pytest
from paper_intensive_reading.bilingual import (
    translate, build_glossary, KNOWN_TERMS
)


class TestTranslate:
    def test_known_term(self):
        result = translate("attention")
        assert "zh" in result
        assert result["zh"] in ["注意力", "关注", "注意力机制"]

    def test_case_insensitive(self):
        result = translate("Attention")
        assert "zh" in result

    def test_unknown_term_returns_en(self):
        result = translate("xyz-abc-12345-unknown")
        assert result["zh"]

    def test_embedding_translation(self):
        result = translate("embedding")
        assert "嵌入" in result["zh"]

    def test_fine_tuning_translation(self):
        result = translate("fine-tuning")
        assert "微调" in result["zh"]


class TestBuildGlossary:
    def test_build_from_terms(self):
        terms = ["attention", "embedding", "transformer"]
        glossary = build_glossary(terms)
        assert "attention" in glossary
        assert "embedding" in glossary
        assert "transformer" in glossary
        assert all("zh" in v for v in glossary.values())

    def test_build_with_descriptions(self):
        glossary = build_glossary(["attention"], with_description=True)
        assert glossary["attention"]["description"]

    def test_dedup(self):
        terms = ["attention", "Attention", "ATTENTION"]
        glossary = build_glossary(terms)
        assert len(glossary) == 1


def test_known_terms_not_empty():
    assert len(KNOWN_TERMS) > 30
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_bilingual.py -v
```

- [ ] **Step 3: 写 bilingual.py**

`paper-intensive-reading/bilingual.py`:
```python
"""中英术语映射。"""

KNOWN_TERMS: dict[str, dict[str, str]] = {
    "transformer": {"zh": "Transformer", "description": "基于自注意力的神经网络架构"},
    "attention": {"zh": "注意力", "description": "让模型关注输入中相关部分"},
    "self-attention": {"zh": "自注意力", "description": "同一序列内部各位置之间的注意力"},
    "cross-attention": {"zh": "交叉注意力", "description": "两个不同序列之间的注意力"},
    "multi-head attention": {"zh": "多头注意力", "description": "并行多组注意力"},
    "encoder": {"zh": "编码器", "description": "将输入映射为表示的模块"},
    "decoder": {"zh": "解码器", "description": "从表示生成输出的模块"},
    "embedding": {"zh": "嵌入", "description": "把离散符号映射为连续向量"},
    "token": {"zh": "词元", "description": "文本的最小处理单位"},
    "tokenization": {"zh": "分词", "description": "把文本切分为词元"},
    "vocabulary": {"zh": "词表", "description": "模型能识别的所有词元集合"},
    "fine-tuning": {"zh": "微调", "description": "在预训练模型上用特定数据继续训练"},
    "pre-training": {"zh": "预训练", "description": "在大规模数据上训练通用模型"},
    "transfer learning": {"zh": "迁移学习", "description": "把已学知识迁移到新任务"},
    "supervised learning": {"zh": "监督学习", "description": "用标注数据训练"},
    "unsupervised learning": {"zh": "无监督学习", "description": "用未标注数据训练"},
    "self-supervised": {"zh": "自监督", "description": "用数据自身作为监督信号"},
    "reinforcement learning": {"zh": "强化学习", "description": "通过奖励信号学习策略"},
    "rlhf": {"zh": "基于人类反馈的强化学习", "description": "RLHF"},
    "reward model": {"zh": "奖励模型", "description": "预测人类偏好的模型"},
    "gradient descent": {"zh": "梯度下降", "description": "沿梯度反方向更新参数"},
    "adam": {"zh": "Adam 优化器", "description": "自适应学习率优化算法"},
    "learning rate": {"zh": "学习率", "description": "参数更新的步长"},
    "batch size": {"zh": "批量大小", "description": "每次迭代用的样本数"},
    "epoch": {"zh": "轮次", "description": "完整过一遍训练集"},
    "backpropagation": {"zh": "反向传播", "description": "从损失反向计算梯度"},
    "layer normalization": {"zh": "层归一化", "description": "LayerNorm，按特征归一化"},
    "layernorm": {"zh": "层归一化", "description": "LayerNorm"},
    "rmsnorm": {"zh": "均方根归一化", "description": "用均方根做归一化，比 LayerNorm 更快"},
    "batch normalization": {"zh": "批归一化", "description": "按批量维度归一化"},
    "batchnorm": {"zh": "批归一化", "description": "BatchNorm"},
    "gelu": {"zh": "GELU 激活", "description": "高斯误差线性单元"},
    "relu": {"zh": "ReLU 激活", "description": "修正线性单元"},
    "sigmoid": {"zh": "Sigmoid", "description": "S 形激活，输出 0-1"},
    "softmax": {"zh": "Softmax", "description": "把向量变成概率分布"},
    "swiglu": {"zh": "SwiGLU", "description": "GLU 变体，用 Swish 激活"},
    "silu": {"zh": "SiLU/Swish", "description": "Sigmoid Linear Unit"},
    "positional encoding": {"zh": "位置编码", "description": "让模型感知序列位置"},
    "rope": {"zh": "旋转位置编码", "description": "RoPE，用旋转矩阵编码相对位置"},
    "llm": {"zh": "大语言模型", "description": "Large Language Model"},
    "foundation model": {"zh": "基础模型", "description": "大规模预训练通用模型"},
    "prompt": {"zh": "提示", "description": "输入给模型的指令或问题"},
    "in-context learning": {"zh": "上下文学习", "description": "在 prompt 里给示例让模型学习"},
    "few-shot": {"zh": "少样本", "description": "在 prompt 里给几个示例"},
    "zero-shot": {"zh": "零样本", "description": "不给示例直接让模型做"},
    "chain-of-thought": {"zh": "思维链", "description": "CoT，让模型逐步推理"},
    "hallucination": {"zh": "幻觉", "description": "模型生成不真实的内容"},
    "agent": {"zh": "智能体", "description": "能自主决策和行动的 AI 系统"},
    "tool use": {"zh": "工具使用", "description": "让 LLM 调用外部工具"},
    "function calling": {"zh": "函数调用", "description": "让 LLM 调用预定义函数"},
    "rag": {"zh": "检索增强生成", "description": "RAG，先检索相关文档再生成"},
    "retrieval": {"zh": "检索", "description": "从知识库找相关信息"},
    "vector database": {"zh": "向量数据库", "description": "存储和检索向量的数据库"},
    "benchmark": {"zh": "基准测试", "description": "标准化的评估任务"},
    "evaluation": {"zh": "评估", "description": "衡量模型性能"},
    "perplexity": {"zh": "困惑度", "description": "PPL，预测质量的逆指标"},
}


def translate(term: str) -> dict[str, str]:
    key = term.strip().lower()
    entry = KNOWN_TERMS.get(key)
    if entry:
        return {"en": term, "zh": entry["zh"], "description": entry.get("description", "")}
    return {"en": term, "zh": term, "description": ""}


def build_glossary(terms: list[str], with_description: bool = True) -> dict[str, dict[str, str]]:
    glossary: dict[str, dict[str, str]] = {}
    for term in terms:
        key = term.strip().lower()
        if key in glossary:
            continue
        entry = translate(term)
        glossary[key] = entry if with_description else {"zh": entry["zh"]}
    return glossary
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_bilingual.py -v
```
Expected: 9 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/bilingual.py tests/unit/test_bilingual.py
git commit -m "feat(bilingual): add Chinese-English AI/ML terminology glossary"
```

---

**P1-P7 完成。** 继续 P8-P17 在 [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md) 和 [plan-part-3.md](2026-06-04-paper-intensive-reading-PLAN-part3.md)。
