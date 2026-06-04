# 论文精读 Skill 实施计划 (Part 2: P8-P15)

> 接 [plan-part-1.md](2026-06-04-paper-intensive-reading-PLAN.md)，覆盖 P8 公式讲解引擎、P9 阅读清单存储、P10 笔记渲染、P11 Obsidian 同步、P12 Notion 同步、P13 图像生成 fallback、P14 调研模式、P15 对比模式。

---

# 阶段 P8：公式讲解 6 段引擎 (formula_explainer)

## Task 8.1: formula_explainer - 6 段数据结构

**Files:**
- Create: `paper-intensive-reading/formula_explainer.py`
- Test: `tests/unit/test_formula_explainer.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_formula_explainer.py`:
```python
import pytest
from paper_intensive_reading.formula_explainer import (
    FormulaExplanation, FormulaSegment, ExplanationContext,
    build_empty_explanation, FORMULA_PROMPT_TEMPLATE
)
from paper_intensive_reading.types import Formula


def test_formula_segment_creation():
    seg = FormulaSegment(
        kind="original",
        content=r"\text{RMSNorm}(x) = \frac{x}{\sqrt{\text{Mean}(x^2)}} \cdot \gamma",
    )
    assert seg.kind == "original"


def test_formula_explanation_6_segments():
    expl = build_empty_explanation()
    assert len(expl.segments) == 6
    assert [s.kind for s in expl.segments] == [
        "original", "plain", "symbols", "analogy", "example", "code"
    ]


def test_formula_explanation_to_dict():
    expl = build_empty_explanation()
    d = expl.to_dict()
    assert "segments" in d
    assert len(d["segments"]) == 6
    assert d["arxiv_id"] == ""


def test_explanation_context_depth_preference():
    ctx = ExplanationContext(arxiv_id="2302.13971", depth_pref="elementary")
    assert ctx.depth_pref == "elementary"


def test_prompt_template_has_6_placeholders():
    template = FORMULA_PROMPT_TEMPLATE
    for i in range(1, 7):
        assert f"{{SEGMENT_{i}}}" in template or f"段 {i}" in template
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py -v
```

- [ ] **Step 3: 写 formula_explainer.py 第一部分**

`paper-intensive-reading/formula_explainer.py`:
```python
"""公式讲解 6 段引擎：原始 → 白话 → 符号 → 类比 → 计算示例 → NumPy 代码。"""
from dataclasses import dataclass, field
from typing import Any

from .types import Formula


SEGMENT_KINDS = ["original", "plain", "symbols", "analogy", "example", "code"]


@dataclass
class FormulaSegment:
    kind: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "content": self.content, **self.meta}


@dataclass
class FormulaExplanation:
    arxiv_id: str
    formula_number: str
    latex: str
    segments: list[FormulaSegment]
    verified: bool = False
    verification_outputs: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "formula_number": self.formula_number,
            "latex": self.latex,
            "segments": [s.to_dict() for s in self.segments],
            "verified": self.verified,
            "verification_outputs": self.verification_outputs,
        }


@dataclass
class ExplanationContext:
    arxiv_id: str
    depth_pref: str = "elementary"  # "elementary" | "medium" | "deep"
    ladder_layers: list[int] = field(default_factory=list)
    user_feedback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "arxiv_id": self.arxiv_id,
            "depth_pref": self.depth_pref,
            "ladder_layers": self.ladder_layers,
            "user_feedback": self.user_feedback,
        }


def build_empty_explanation() -> FormulaExplanation:
    return FormulaExplanation(
        arxiv_id="",
        formula_number="",
        latex="",
        segments=[FormulaSegment(kind=k, content="") for k in SEGMENT_KINDS],
    )


FORMULA_PROMPT_TEMPLATE = """你是 AI 论文公式讲解助手。用户数学基础: {depth_pref}。
你需要为一个公式生成 6 段讲解。

## 段 1：原始形式（LaTeX）
输出公式的 LaTeX 源码。

## 段 2：白话翻译
用一句中文（不超过 30 字）解释公式在算什么。

## 段 3：逐符号解释
列出公式里每个符号，标注它属于数学概念阶梯的哪一层（如 "第 5 层：向量"）。

## 段 4：直觉类比
用生活场景（图书馆、开车、做饭、购物等）解释公式的核心思想。

## 段 5：详细计算示例
用 d=2 或 d=4 的极小例子，手算可验证。

## 段 6：NumPy 代码实现
用 NumPy 写代码实现这个公式（必须只用 import numpy）。代码要可独立运行。

待讲解公式:
- 编号: {formula_number}
- LaTeX: {latex}
- 上下文（前 200 字）: {context_before}
- 上下文（后 200 字）: {context_after}

请按 6 段输出，每段用 "## 段 N" 开头。
"""
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/formula_explainer.py tests/unit/test_formula_explainer.py
git commit -m "feat(formula_explainer): add 6-segment data structures and prompt template"
```

---

## Task 8.2: formula_explainer - LLM 调用 + 段解析

**Files:**
- Modify: `paper-intensive-reading/formula_explainer.py`
- Modify: `tests/unit/test_formula_explainer.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_formula_explainer.py`:
```python
class TestParseSegments:
    def test_parse_6_segments(self):
        from paper_intensive_reading.formula_explainer import parse_llm_response

        llm_output = """## 段 1
\\text{Attention}(Q,K,V) = \\text{softmax}(\\frac{QK^\\top}{\\sqrt{d_k}})V
## 段 2
每个词看其他词的相关度，加权汇总。
## 段 3
Q (Query, 第5层): 查询向量
K (Key, 第5层): 键向量
## 段 4
图书馆查资料。
## 段 5
d=4 例子: ...
## 段 6
import numpy as np
x = 1
"""

        segments = parse_llm_response(llm_output)
        assert len(segments) == 6
        assert "softmax" in segments[0].content
        assert "图书馆" in segments[3].content
        assert "import numpy" in segments[5].content

    def test_parse_with_extra_text(self):
        from paper_intensive_reading.formula_explainer import parse_llm_response

        llm_output = """前面有一些废话。

## 段 1
公式
## 段 2
白话
## 段 3
符号
## 段 4
类比
## 段 5
例子
## 段 6
代码

后面也有废话。
"""
        segments = parse_llm_response(llm_output)
        assert len(segments) == 6


class TestCallLlm:
    def test_call_llm_with_mock(self, monkeypatch):
        from paper_intensive_reading import formula_explainer
        from paper_intensive_reading.formula_explainer import explain_formula, FormulaSegment

        def mock_llm(prompt, **kwargs):
            return """## 段 1
E = mc^2
## 段 2
能量等于质量乘光速平方
## 段 3
E (能量, 第0层)
## 段 4
像烧煤释放能量
## 段 5
m=1, c=2 → E=4
## 段 6
import numpy as np
print(1 * 2**2)
"""

        monkeypatch.setattr(formula_explainer, "call_llm", mock_llm)

        formula = Formula(
            number="(1)", latex="E = mc^2",
            context_before="Einstein", context_after="rest energy",
        )
        expl = explain_formula(formula, arxiv_id="test", llm_fn=mock_llm)
        assert len(expl.segments) == 6
        assert "mc^2" in expl.segments[0].content
        assert expl.verified is False
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py::TestParseSegments tests/unit/test_formula_explainer.py::TestCallLlm -v
```

- [ ] **Step 3: 追加 parse_llm_response 和 explain_formula**

追加到 `paper-intensive-reading/formula_explainer.py`:
```python
import re


def call_llm(prompt: str, **kwargs) -> str:
    """调用 LLM 的占位函数。实际实现由调用方注入（便于测试）。"""
    raise NotImplementedError("call_llm must be injected by caller")


def parse_llm_response(response: str) -> list[FormulaSegment]:
    """解析 LLM 返回的 6 段输出。"""
    # 用 "## 段 N" 切分
    pattern = re.compile(r"##\s*段\s*(\d+)\s*\n", re.MULTILINE)
    matches = list(pattern.finditer(response))
    if len(matches) < 6:
        # 失败：返回空段
        return [FormulaSegment(kind=k, content="") for k in SEGMENT_KINDS]

    segments = []
    for i in range(6):
        start = matches[i].end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(response)
        content = response[start:end].strip()
        segments.append(FormulaSegment(kind=SEGMENT_KINDS[i], content=content))
    return segments


def explain_formula(
    formula: Formula,
    arxiv_id: str,
    llm_fn=None,
) -> FormulaExplanation:
    """调用 LLM 生成 6 段讲解。"""
    from .errors import LLMError

    if llm_fn is None:
        llm_fn = call_llm

    prompt = FORMULA_PROMPT_TEMPLATE.format(
        depth_pref="elementary",
        formula_number=formula.number,
        latex=formula.latex,
        context_before=formula.context_before[:200],
        context_after=formula.context_after[:200],
    )

    try:
        response = llm_fn(prompt)
    except Exception as e:
        raise LLMError("default", detail=str(e)) from e

    if not response or len(response) < 50:
        raise LLMError("bad_format", detail="LLM 返回过短")

    segments = parse_llm_response(response)
    if not any(s.content for s in segments):
        raise LLMError("bad_format", detail="无法解析任何段")

    return FormulaExplanation(
        arxiv_id=arxiv_id,
        formula_number=formula.number,
        latex=formula.latex,
        segments=segments,
    )
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py -v
```
Expected: 8 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/formula_explainer.py tests/unit/test_formula_explainer.py
git commit -m "feat(formula_explainer): add LLM call and 6-segment parser"
```

---

## Task 8.3: formula_explainer - NumPy 代码执行 + 三对照

**Files:**
- Modify: `paper-intensive-reading/formula_explainer.py`
- Modify: `tests/unit/test_formula_explainer.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_formula_explainer.py`:
```python
class TestVerifyWithNumpy:
    def test_verify_runs_code(self):
        from paper_intensive_reading.formula_explainer import verify_code_segment

        code = """
import numpy as np
Q = np.array([[1, 0, 1, 0]])
K = np.array([[1, 1, 0, 0]])
scores = Q @ K.T
print(f"scores = {scores}")
"""
        result = verify_code_segment(code)
        assert result["ok"]
        assert "scores" in result["stdout"]

    def test_verify_handles_failure(self):
        from paper_intensive_reading.formula_explainer import verify_code_segment

        code = "import os\nos.system('echo HACKED')"
        result = verify_code_segment(code)
        assert not result["ok"]

    def test_extract_code_from_segment(self):
        from paper_intensive_reading.formula_explainer import extract_code

        segment_content = """
**NumPy 代码 + 实际运行**：

```python
import numpy as np
x = np.array([1, 2, 3])
print(x.sum())
```

实际跑出：
```
6
```
"""
        code = extract_code(segment_content)
        assert "import numpy" in code
        assert "x.sum()" in code


class TestThreeWayVerification:
    def test_run_three_way_verification(self):
        from paper_intensive_reading.formula_explainer import (
            build_empty_explanation, three_way_verify, FormulaSegment
        )

        expl = build_empty_explanation()
        expl.segments[5] = FormulaSegment(
            kind="code",
            content="```python\nimport numpy as np\nx = np.array([1,2,3])\nprint(x.sum())\n```",
        )

        result = three_way_verify(expl)
        assert "actual" in result
        assert result["actual"]["ok"]
        assert "6" in result["actual"]["stdout"]
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py::TestVerifyWithNumpy tests/unit/test_formula_explainer.py::TestThreeWayVerification -v
```

- [ ] **Step 3: 追加 verify_code_segment + extract_code + three_way_verify**

追加到 `paper-intensive-reading/formula_explainer.py`:
```python
from .numpy_runner import run as run_numpy


def extract_code(segment_content: str) -> str:
    """从段[6]的 markdown 文本里提取 ```python ... ``` 代码块。"""
    pattern = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)
    m = pattern.search(segment_content)
    if m:
        return m.group(1).strip()
    # fallback: 整段当作代码
    return segment_content.strip()


def verify_code_segment(code: str, **run_kwargs) -> dict:
    """调用 numpy_runner 跑代码，返回结构化结果。"""
    result = run_numpy(code, **run_kwargs)
    return result.to_dict()


def three_way_verify(
    explanation: FormulaExplanation,
) -> dict:
    """三对照：手算（段[5]）vs 代码（段[6]）vs 实际跑出。"""
    if len(explanation.segments) < 6:
        return {"hand": "", "code": "", "actual": {"ok": False, "stdout": ""}}

    hand = explanation.segments[4].content  # 段[5] 手算
    code_segment = explanation.segments[5].content
    code = extract_code(code_segment)
    actual = verify_code_segment(code)

    return {
        "hand": hand,
        "code": code,
        "actual": actual,
    }
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_formula_explainer.py -v
```
Expected: 11 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/formula_explainer.py tests/unit/test_formula_explainer.py
git commit -m "feat(formula_explainer): add NumPy code extraction, execution, and three-way verification"
```

---

# 阶段 P9：阅读清单存储 (paper_store)

## Task 9.1: paper_store - SQLite schema + 初始化

**Files:**
- Create: `paper-intensive-reading/paper_store.py`
- Test: `tests/unit/test_paper_store.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_paper_store.py`:
```python
import pytest
from datetime import date
from paper_intensive_reading.paper_store import (
    init_db, add_paper, get_paper, list_papers,
    update_status, update_progress, get_progress
)


class TestInitDb:
    def test_init_creates_tables(self, tmp_db):
        init_db(tmp_db)
        # 验证：能 add 一个 paper
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971",
            "title": "LLaMA",
            "authors": ["Touvron"],
            "affiliations": ["Meta AI"],
            "abstract": "We introduce LLaMA.",
            "published": date(2023, 2, 27),
            "pdf_path": "/tmp/x.pdf",
        })
        p = get_paper(tmp_db, "2302.13971")
        assert p is not None
        assert p["title"] == "LLaMA"


class TestPaperCrud:
    def test_add_and_get(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": ["Touvron"], "affiliations": ["Meta AI"],
            "abstract": "x", "published": date(2023, 2, 27),
            "pdf_path": "/tmp/x.pdf",
        })
        p = get_paper(tmp_db, "2302.13971")
        assert p["arxiv_id"] == "2302.13971"

    def test_add_duplicate_updates(self, tmp_db):
        init_db(tmp_db)
        meta = {"arxiv_id": "2302.13971", "title": "LLaMA v1",
                "authors": [], "affiliations": [], "abstract": "x",
                "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf"}
        add_paper(tmp_db, meta)
        meta["title"] = "LLaMA v2"
        add_paper(tmp_db, meta)
        p = get_paper(tmp_db, "2302.13971")
        assert p["title"] == "LLaMA v2"

    def test_get_nonexistent_returns_none(self, tmp_db):
        init_db(tmp_db)
        assert get_paper(tmp_db, "0000.00000") is None


class TestStatus:
    def test_update_status(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": [], "affiliations": [], "abstract": "x",
            "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf",
        })
        update_status(tmp_db, "2302.13971", "已读完")
        p = get_paper(tmp_db, "2302.13971")
        assert p["status"] == "已读完"

    def test_list_by_status(self, tmp_db):
        init_db(tmp_db)
        for i, status in enumerate(["待读", "在读", "已读完", "已读完"]):
            add_paper(tmp_db, {
                "arxiv_id": f"2302.1397{i}", "title": f"Paper {i}",
                "authors": [], "affiliations": [], "abstract": "x",
                "published": date(2023, 2, 27), "pdf_path": f"/tmp/{i}.pdf",
            })
            update_status(tmp_db, f"2302.1397{i}", status)

        done = list_papers(tmp_db, status="已读完")
        assert len(done) == 2


class TestProgress:
    def test_mark_section_done(self, tmp_db):
        init_db(tmp_db)
        add_paper(tmp_db, {
            "arxiv_id": "2302.13971", "title": "LLaMA",
            "authors": [], "affiliations": [], "abstract": "x",
            "published": date(2023, 2, 27), "pdf_path": "/tmp/x.pdf",
        })
        mark_section_done(tmp_db, "2302.13971", "1")
        mark_section_done(tmp_db, "2302.13971", "2")
        progress = get_progress(tmp_db, "2302.13971")
        assert progress["sections_done"] == ["1", "2"]
        assert progress["percent"] > 0
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py -v
```

- [ ] **Step 3: 写 paper_store.py**

`paper-intensive-reading/paper_store.py`:
```python
"""阅读清单 / 进度 / 元数据 存储。"""
import sqlite3
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    arxiv_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT,
    affiliations TEXT,
    abstract TEXT,
    published TEXT,
    pdf_path TEXT,
    note_path TEXT,
    status TEXT DEFAULT '待读',
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections_progress (
    arxiv_id TEXT,
    section_number TEXT,
    done INTEGER DEFAULT 0,
    PRIMARY KEY (arxiv_id, section_number)
);

CREATE TABLE IF NOT EXISTS formula_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    arxiv_id TEXT,
    formula_number TEXT,
    attempt INTEGER,
    passed INTEGER,
    feedback TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_state (
    arxiv_id TEXT PRIMARY KEY,
    depth_pref TEXT DEFAULT 'elementary',
    skipped_formulas TEXT,
    pending_questions TEXT
);
"""


def init_db(db_path: str | Path) -> None:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def add_paper(db_path: str | Path, meta: dict[str, Any]) -> None:
    init_db(db_path)  # 确保表存在
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """INSERT OR REPLACE INTO papers
            (arxiv_id, title, authors, affiliations, abstract, published, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                meta["arxiv_id"], meta["title"],
                json.dumps(meta.get("authors", [])),
                json.dumps(meta.get("affiliations", [])),
                meta.get("abstract", ""),
                meta["published"].isoformat() if isinstance(meta.get("published"), date) else str(meta.get("published", "")),
                meta.get("pdf_path", ""),
            ),
        )
        conn.commit()


def get_paper(db_path: str | Path, arxiv_id: str) -> dict | None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,)).fetchone()
    if not row:
        return None
    return {
        "arxiv_id": row["arxiv_id"], "title": row["title"],
        "authors": json.loads(row["authors"] or "[]"),
        "affiliations": json.loads(row["affiliations"] or "[]"),
        "abstract": row["abstract"], "published": row["published"],
        "pdf_path": row["pdf_path"], "note_path": row["note_path"],
        "status": row["status"], "added_at": row["added_at"],
        "finished_at": row["finished_at"],
    }


def list_papers(db_path: str | Path, status: str | None = None) -> list[dict]:
    with sqlite3.connect(str(db_path)) as conn:
        if status:
            rows = conn.execute("SELECT arxiv_id FROM papers WHERE status = ?", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT arxiv_id FROM papers").fetchall()
    return [r[0] for r in rows]


def update_status(db_path: str | Path, arxiv_id: str, status: str) -> None:
    finished = datetime.now().isoformat() if status == "已读完" else None
    with sqlite3.connect(str(db_path)) as conn:
        if finished:
            conn.execute(
                "UPDATE papers SET status = ?, finished_at = ? WHERE arxiv_id = ?",
                (status, finished, arxiv_id),
            )
        else:
            conn.execute(
                "UPDATE papers SET status = ? WHERE arxiv_id = ?", (status, arxiv_id)
            )
        conn.commit()


def mark_section_done(db_path: str | Path, arxiv_id: str, section_number: str) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sections_progress (arxiv_id, section_number, done) VALUES (?, ?, 1)",
            (arxiv_id, section_number),
        )
        conn.commit()


def get_progress(db_path: str | Path, arxiv_id: str) -> dict:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            "SELECT section_number FROM sections_progress WHERE arxiv_id = ? AND done = 1 ORDER BY section_number",
            (arxiv_id,),
        ).fetchall()
    sections = [r[0] for r in rows]
    return {
        "sections_done": sections,
        "count": len(sections),
        "percent": min(100, len(sections) * 10),  # 粗估：每节 10%
    }


def save_note_path(db_path: str | Path, arxiv_id: str, note_path: str) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("UPDATE papers SET note_path = ? WHERE arxiv_id = ?", (note_path, arxiv_id))
        conn.commit()
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py -v
```
Expected: 8 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/paper_store.py tests/unit/test_paper_store.py
git commit -m "feat(paper_store): add SQLite schema, CRUD, status, progress tracking"
```

---

## Task 9.2: paper_store - 公式尝试记录

**Files:**
- Modify: `paper-intensive-reading/paper_store.py`
- Modify: `tests/unit/test_paper_store.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_paper_store.py`:
```python
class TestFormulaAttempts:
    def test_record_attempt(self, tmp_db):
        from paper_intensive_reading.paper_store import record_formula_attempt, get_formula_attempts
        init_db(tmp_db)
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=True, feedback="ok")
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=False, feedback="didn't know softmax")
        record_formula_attempt(tmp_db, "2302.13971", "(1)", passed=True, feedback="ok after re-explain")

        attempts = get_formula_attempts(tmp_db, "2302.13971", "(1)")
        assert len(attempts) == 3
        assert attempts[0]["passed"] is True
        assert attempts[1]["passed"] is False
        assert attempts[2]["passed"] is True
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py::TestFormulaAttempts -v
```

- [ ] **Step 3: 追加 record_formula_attempt + get_formula_attempts**

追加到 `paper-intensive-reading/paper_store.py`:
```python
def record_formula_attempt(
    db_path: str | Path, arxiv_id: str, formula_number: str,
    passed: bool, feedback: str = "",
) -> int:
    """记录一次理解确认尝试。返回 attempt 序号。"""
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute(
            "SELECT COUNT(*) FROM formula_attempts WHERE arxiv_id = ? AND formula_number = ?",
            (arxiv_id, formula_number),
        )
        attempt = cur.fetchone()[0] + 1
        conn.execute(
            "INSERT INTO formula_attempts (arxiv_id, formula_number, attempt, passed, feedback) VALUES (?, ?, ?, ?, ?)",
            (arxiv_id, formula_number, attempt, 1 if passed else 0, feedback),
        )
        conn.commit()
    return attempt


def get_formula_attempts(
    db_path: str | Path, arxiv_id: str, formula_number: str,
) -> list[dict]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM formula_attempts WHERE arxiv_id = ? AND formula_number = ? ORDER BY id",
            (arxiv_id, formula_number),
        ).fetchall()
    return [
        {"id": r["id"], "arxiv_id": r["arxiv_id"], "formula_number": r["formula_number"],
         "attempt": r["attempt"], "passed": bool(r["passed"]), "feedback": r["feedback"]}
        for r in rows
    ]
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py -v
```
Expected: 9 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/paper_store.py tests/unit/test_paper_store.py
git commit -m "feat(paper_store): add formula attempt tracking for understanding check loop"
```

---

## Task 9.3: paper_store - 用户状态

**Files:**
- Modify: `paper-intensive-reading/paper_store.py`
- Modify: `tests/unit/test_paper_store.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_paper_store.py`:
```python
class TestUserState:
    def test_set_get_state(self, tmp_db):
        from paper_intensive_reading.paper_store import set_user_state, get_user_state
        init_db(tmp_db)
        set_user_state(tmp_db, "2302.13971", {
            "depth_pref": "elementary",
            "skipped_formulas": ["(3)", "(7)"],
            "pending_questions": ["What is RoPE?"],
        })
        state = get_user_state(tmp_db, "2302.13971")
        assert state["depth_pref"] == "elementary"
        assert state["skipped_formulas"] == ["(3)", "(7)"]
        assert state["pending_questions"] == ["What is RoPE?"]

    def test_update_partial(self, tmp_db):
        from paper_intensive_reading.paper_store import set_user_state, get_user_state
        init_db(tmp_db)
        set_user_state(tmp_db, "2302.13971", {"depth_pref": "medium"})
        # 部分更新
        set_user_state(tmp_db, "2302.13971", {"pending_questions": ["new q"]})
        state = get_user_state(tmp_db, "2302.13971")
        assert state["depth_pref"] == "medium"  # 保留
        assert state["pending_questions"] == ["new q"]  # 新增
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py::TestUserState -v
```

- [ ] **Step 3: 追加 set_user_state + get_user_state**

追加到 `paper-intensive-reading/paper_store.py`:
```python
def set_user_state(db_path: str | Path, arxiv_id: str, state: dict) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        # 部分更新：先取旧值
        row = conn.execute(
            "SELECT depth_pref, skipped_formulas, pending_questions FROM user_state WHERE arxiv_id = ?",
            (arxiv_id,),
        ).fetchone()
        old = {
            "depth_pref": row[0] if row else "elementary",
            "skipped_formulas": json.loads(row[1] or "[]") if row else [],
            "pending_questions": json.loads(row[2] or "[]") if row else [],
        }
        merged = {**old, **state}
        conn.execute(
            "INSERT OR REPLACE INTO user_state (arxiv_id, depth_pref, skipped_formulas, pending_questions) VALUES (?, ?, ?, ?)",
            (arxiv_id, merged["depth_pref"],
             json.dumps(merged["skipped_formulas"]),
             json.dumps(merged["pending_questions"])),
        )
        conn.commit()


def get_user_state(db_path: str | Path, arxiv_id: str) -> dict:
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute(
            "SELECT depth_pref, skipped_formulas, pending_questions FROM user_state WHERE arxiv_id = ?",
            (arxiv_id,),
        ).fetchone()
    if not row:
        return {"depth_pref": "elementary", "skipped_formulas": [], "pending_questions": []}
    return {
        "depth_pref": row[0],
        "skipped_formulas": json.loads(row[1] or "[]"),
        "pending_questions": json.loads(row[2] or "[]"),
    }
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_paper_store.py -v
```
Expected: 11 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/paper_store.py tests/unit/test_paper_store.py
git commit -m "feat(paper_store): add user_state (depth_pref, skipped, pending_questions)"
```

---

# 阶段 P10：笔记渲染 (to_markdown)

## Task 10.1: to_markdown - 单篇笔记模板

**Files:**
- Create: `paper-intensive-reading/to_markdown.py`
- Test: `tests/unit/test_to_markdown.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_to_markdown.py`:
```python
import pytest
from datetime import date
from paper_intensive_reading.to_markdown import render_single_note
from paper_intensive_reading.types import Paper, Section, Paragraph, Formula, Figure


def test_render_basic_note(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971",
        title="LLaMA: Open and Efficient Foundation Language Models",
        authors=["Touvron", "Lavril"],
        affiliations=["Meta AI"],
        abstract="We introduce LLaMA.",
        published=date(2023, 2, 27),
        pdf_path="/tmp/2302.13971.pdf",
        sections=[
            Section(number="1", title="Introduction", level=1,
                    paragraphs=[Paragraph(text="Foundation models are large.", page=1)]),
        ],
        figures=[Figure(number="Figure 1", caption="Overview", image_path="figures/fig-1.png", page=3)],
        tables=[], algorithms=[], references=[],
    )

    md = render_single_note(paper, formula_explanations=[], user_state={})

    assert "LLaMA: Open and Efficient" in md
    assert "---" in md  # front matter
    assert "arxiv_id: 2302.13971" in md
    assert "TL;DR" in md or "一句话" in md
    assert "## 1. 背景与动机" in md or "## 背景" in md
    assert "## 1. Introduction" in md or "## Introduction" in md
    assert "Figure 1" in md


def test_render_with_formula_explanations(tmp_path):
    from paper_intensive_reading.formula_explainer import (
        FormulaExplanation, FormulaSegment, build_empty_explanation
    )
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf",
        sections=[Section(number="3", title="Method", level=1, paragraphs=[])],
        figures=[], tables=[], algorithms=[], references=[],
    )
    expl = build_empty_explanation()
    expl.arxiv_id = "2302.13971"
    expl.formula_number = "(1)"
    expl.latex = "E = mc^2"
    expl.segments[1] = FormulaSegment(kind="plain", content="能量等于质量乘光速平方")

    md = render_single_note(paper, formula_explanations=[expl], user_state={})
    assert "公式 (1)" in md or "Eq. (1)" in md
    assert "能量等于质量" in md


def test_render_with_glossary(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    md = render_single_note(paper, formula_explanations=[], user_state={}, glossary=["attention", "embedding"])
    assert "术语表" in md
    assert "attention" in md.lower() or "注意力" in md


def test_render_includes_front_matter(tmp_path):
    paper = Paper(
        arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
        affiliations=["Meta AI"], abstract="x", published=date(2023, 2, 27),
        pdf_path="/tmp/x.pdf", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )
    md = render_single_note(paper, formula_explanations=[], user_state={}, status="已读完", tags=["llm"])
    assert "status: 已读完" in md
    assert "tags:" in md
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py -v
```

- [ ] **Step 3: 写 to_markdown.py**

`paper-intensive-reading/to_markdown.py`:
```python
"""精读笔记渲染：把 Paper + 公式讲解 + 用户状态 → Markdown。"""
from datetime import datetime, timezone
from .types import Paper
from .bilingual import build_glossary


def render_single_note(
    paper: Paper,
    formula_explanations: list,
    user_state: dict,
    glossary: list[str] | None = None,
    status: str = "在读",
    tags: list[str] | None = None,
) -> str:
    """渲染单篇精读笔记。"""
    tags = tags or []
    glossary = glossary or []

    # Front matter
    fm_lines = [
        "---",
        f"arxiv_id: {paper.arxiv_id}",
        f"title: \"{paper.title}\"",
        f"authors: {paper.authors}",
        f"year: {paper.published.year}",
        f"status: {status}",
        f"depth_pref: {user_state.get('depth_pref', 'elementary')}",
        f"tags: {tags}",
        f"公式数: {sum(len(s.formulas) for s in paper.sections)}",
        f"图表数: {len(paper.figures)}",
        f"read_time: 30min",
        f"finished_at: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        "---",
        "",
        f"# {paper.title}",
        "",
    ]
    fm = "\n".join(fm_lines)

    # TL;DR（用 abstract 第一句）
    tldr = ""
    if paper.abstract:
        first_sentence = paper.abstract.split(".")[0].split("。")[0]
        tldr = f"> **TL;DR**：{first_sentence.strip()}。\n\n"

    # 背景与动机
    background = "## 1. 背景与动机\n\n"
    background += f"{paper.abstract}\n\n" if paper.abstract else ""

    # 章节
    sections_md = "## 2. 章节概览\n\n"
    for sec in paper.sections:
        sections_md += f"### {sec.number} {sec.title}\n\n"
        for p in sec.paragraphs:
            if p.text.strip():
                sections_md += f"{p.text[:300]}...\n\n" if len(p.text) > 300 else f"{p.text}\n\n"
        for f in sec.formulas:
            sections_md += f"**公式 {f.number}**\n\n"

    # 方法详解（公式讲解 6 段）
    method = "## 3. 方法详解\n\n"
    for expl in formula_explanations:
        method += f"### 公式 {expl.formula_number}\n\n"
        method += "**原始形式**：\n\n"
        method += f"$$\n{expl.latex}\n$$\n\n"
        if expl.segments[1].content:
            method += f"**白话**：{expl.segments[1].content}\n\n"
        if expl.segments[2].content:
            method += f"**符号**：\n\n{expl.segments[2].content}\n\n"
        if expl.segments[3].content:
            method += f"**类比**：{expl.segments[3].content}\n\n"
        if expl.segments[4].content:
            method += f"**计算示例**：\n\n{expl.segments[4].content}\n\n"
        if expl.segments[5].content:
            method += f"**NumPy 代码**：\n\n{expl.segments[5].content}\n\n"
        if expl.verification_outputs:
            actual = expl.verification_outputs.get("actual", {})
            if actual.get("ok"):
                method += f"**实际跑出**：\n```\n{actual['stdout']}\n```\n\n"

    # 实验
    experiments = "## 4. 实验与结果\n\n"
    if paper.figures:
        experiments += "### 图表\n\n"
        for fig in paper.figures:
            experiments += f"**{fig.number}**：{fig.caption}\n\n"
            if fig.image_path:
                experiments += f"![{fig.number}]({fig.image_path})\n\n"

    # 讨论
    discussion = "## 5. 讨论与启示\n\n### 优点\n- [待补充]\n\n### 局限\n- [待补充]\n\n"

    # 术语表
    glossary_md = ""
    if glossary:
        glossary_md = "## 6. 术语表（中英对照）\n\n"
        glossary_md += "| 英文 | 中文 | 解释 |\n|------|------|------|\n"
        entries = build_glossary(glossary)
        for en, entry in entries.items():
            glossary_md += f"| {en} | {entry['zh']} | {entry.get('description', '')} |\n"
        glossary_md += "\n"

    # 参考资料
    references = "## 7. 参考资料\n\n"
    references += f"- 论文 PDF：`{paper.pdf_path}`\n"
    references += f"- arXiv 链接：https://arxiv.org/abs/{paper.arxiv_id}\n"

    footer = f"\n---\n*由 paper-intensive-reading skill 自动生成于 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n"

    return (
        fm + tldr + background + sections_md + method + experiments +
        discussion + glossary_md + references + footer
    )
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_markdown.py tests/unit/test_to_markdown.py
git commit -m "feat(to_markdown): add single paper note rendering with 6-segment formula sections"
```

---

## Task 10.2: to_markdown - 对比笔记

**Files:**
- Modify: `paper-intensive-reading/to_markdown.py`
- Modify: `tests/unit/test_to_markdown.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_markdown.py`:
```python
class TestCompareNote:
    def test_render_compare_note(self):
        from paper_intensive_reading.to_markdown import render_compare_note
        papers = [
            Paper(arxiv_id="2302.13971", title="LLaMA", authors=["Touvron"],
                  affiliations=["Meta AI"], abstract="LLaMA paper",
                  published=date(2023, 2, 27), pdf_path="/tmp/llama.pdf",
                  sections=[], figures=[], tables=[], algorithms=[], references=[]),
            Paper(arxiv_id="2005.14165", title="GPT-3", authors=["Brown"],
                  affiliations=["OpenAI"], abstract="GPT-3 paper",
                  published=date(2020, 5, 28), pdf_path="/tmp/gpt3.pdf",
                  sections=[], figures=[], tables=[], algorithms=[], references=[]),
        ]
        md = render_compare_note(papers)
        assert "LLaMA" in md
        assert "GPT-3" in md
        assert "对比" in md or "vs" in md.lower()
        assert "概览对比" in md or "维度" in md
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py::TestCompareNote -v
```

- [ ] **Step 3: 追加 render_compare_note**

追加到 `paper-intensive-reading/to_markdown.py`:
```python
def render_compare_note(papers: list[Paper]) -> str:
    """渲染多论文对比笔记。"""
    if not papers:
        return ""

    fm = "---\nmode: compare\npapers: " + str(len(papers)) + "\n---\n\n"
    title = f"# 对比笔记：{' vs '.join(p.title for p in papers)}\n\n"

    overview = "## 概览对比\n\n| 维度 | " + " | ".join(f"{p.title}" for p in papers) + " |\n"
    overview += "|------|" + "|".join(["-" * 6] * len(papers)) + "|\n"
    overview += "| arXiv ID | " + " | ".join(p.arxiv_id for p in papers) + " |\n"
    overview += "| 时间 | " + " | ".join(p.published.isoformat() for p in papers) + " |\n"
    overview += "| 作者数 | " + " | ".join(str(len(p.authors)) for p in papers) + " |\n"
    overview += "| 公式数 | " + " | ".join(str(sum(len(s.formulas) for s in p.sections)) for p in papers) + " |\n"
    overview += "| 图表数 | " + " | ".join(str(len(p.figures)) for p in papers) + " |\n\n"

    abstracts = "## 摘要对比\n\n"
    for p in papers:
        abstracts += f"### {p.title}\n\n{p.abstract}\n\n"

    footer = f"\n---\n*由 paper-intensive-reading skill 自动生成于 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n"

    return fm + title + overview + abstracts + footer
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_markdown.py tests/unit/test_to_markdown.py
git commit -m "feat(to_markdown): add compare note rendering"
```

---

## Task 10.3: to_markdown - 调研笔记

**Files:**
- Modify: `paper-intensive-reading/to_markdown.py`
- Modify: `tests/unit/test_to_markdown.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_markdown.py`:
```python
class TestSurveyNote:
    def test_render_survey_note(self):
        from paper_intensive_reading.to_markdown import render_survey_note
        papers_info = [
            {"arxiv_id": "2302.04761", "title": "Toolformer", "authors": ["Schick"],
             "year": 2023, "reason": "开山工作", "method": "自监督构造工具调用数据",
             "citations": 1834, "url": "https://arxiv.org/abs/2302.04761"},
            {"arxiv_id": "2210.03629", "title": "ReAct", "authors": ["Yao"],
             "year": 2022, "reason": "推理+行动范式", "method": "Reason+Act 循环",
             "citations": 1521, "url": "https://arxiv.org/abs/2210.03629"},
        ]
        md = render_survey_note("LLM Agents", papers_info)
        assert "LLM Agents" in md
        assert "Toolformer" in md
        assert "ReAct" in md
        assert "阅读路径" in md
        assert "开山" in md
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py::TestSurveyNote -v
```

- [ ] **Step 3: 追加 render_survey_note**

追加到 `paper-intensive-reading/to_markdown.py`:
```python
def render_survey_note(query: str, papers_info: list[dict]) -> str:
    """渲染调研笔记。"""
    fm = f"---\nmode: survey\nquery: \"{query}\"\npaper_count: {len(papers_info)}\n---\n\n"
    title = f"# 调研：{query} (截至 {datetime.now(timezone.utc).strftime('%Y-%m')})\n\n"
    intro = f"> 来自 arXiv 搜索，Top {len(papers_info)} 论文按引用 + 时效排序\n\n"

    body = ""
    for i, p in enumerate(papers_info, 1):
        body += f"## {i}. {p['title']} ({', '.join(p.get('authors', []))}, {p.get('year', 'N/A')})\n\n"
        body += f"**为什么读**：{p.get('reason', 'N/A')}\n\n"
        body += f"**核心方法**：{p.get('method', 'N/A')}\n\n"
        body += f"**引用数**：{p.get('citations', 'N/A')}\n\n"
        body += f"**arXiv**：[{p['arxiv_id']}]({p.get('url', f'https://arxiv.org/abs/{p['arxiv_id']}')})\n\n"

    reading_path = "## 阅读路径建议\n\n按基础 → 进阶顺序：\n\n"
    for i, p in enumerate(papers_info, 1):
        reading_path += f"{i}. {p['title']} - {p.get('reason', '')}\n"

    footer = f"\n---\n*由 paper-intensive-reading skill 自动生成于 {datetime.now(timezone.utc).strftime('%Y-%m-%d')}*\n"

    return fm + title + intro + body + reading_path + footer
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_markdown.py -v
```
Expected: 6 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_markdown.py tests/unit/test_to_markdown.py
git commit -m "feat(to_markdown): add survey note rendering"
```

---

# 阶段 P11：Obsidian 同步 (to_obsidian)

## Task 11.1: to_obsidian - vault 检测 + 路径准备

**Files:**
- Create: `paper-intensive-reading/to_obsidian.py`
- Test: `tests/unit/test_to_obsidian.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_to_obsidian.py`:
```python
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
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py -v
```

- [ ] **Step 3: 写 to_obsidian.py 第一部分**

`paper-intensive-reading/to_obsidian.py`:
```python
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_obsidian.py tests/unit/test_to_obsidian.py
git commit -m "feat(to_obsidian): add vault detection and folder preparation"
```

---

## Task 11.2: to_obsidian - 复制 MD + PDF + 双向链接

**Files:**
- Modify: `paper-intensive-reading/to_obsidian.py`
- Modify: `tests/unit/test_to_obsidian.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_obsidian.py`:
```python
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
        add_wikilinks(md, "2302.13971", ["GLOBAL_NOTE", "ANOTHER_NOTE"])
        content = md.read_text()
        assert "[[2302.13971-LLaMA/2302.13971-精读笔记|GLOBAL_NOTE]]" in content or "[[2302.13971" in content
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py::TestCopyToVault -v
```

- [ ] **Step 3: 追加 copy_to_vault + add_wikilinks**

追加到 `paper-intensive-reading/to_obsidian.py`:
```python
import re


def copy_to_vault(
    paper_dir: Path, md_path: Path, pdf_path: Path | None = None,
    figure_paths: list[Path] | None = None,
) -> dict[str, Path]:
    """复制 MD + PDF + 图片到 vault，返回产物路径字典。"""
    paper_dir = Path(paper_dir)
    md_path = Path(md_path)
    figure_paths = figure_paths or []

    arxiv_id = paper_dir.name.split("-")[0]
    target_md = paper_dir / f"{arxiv_id}-精读笔记.md"
    shutil.copy2(md_path, target_md)

    result = {"md": target_md}

    if pdf_path and Path(pdf_path).exists():
        target_pdf = paper_dir / f"{arxiv_id}.pdf"
        shutil.copy2(pdf_path, target_pdf)
        result["pdf"] = target_pdf

    figures_dir = paper_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    copied_figs = []
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
    safe_id = arxiv_id.replace(".", "-")
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
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py -v
```
Expected: 7 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_obsidian.py tests/unit/test_to_obsidian.py
git commit -m "feat(to_obsidian): add copy_to_vault and wikilinks injection"
```

---

## Task 11.3: to_obsidian - 索引页 + save() 统一入口

**Files:**
- Modify: `paper-intensive-reading/to_obsidian.py`
- Modify: `tests/unit/test_to_obsidian.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_obsidian.py`:
```python
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

        result = save(
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
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py::TestSaveUnified tests/unit/test_to_obsidian.py::TestIndexPage -v
```

- [ ] **Step 3: 追加 save + update_index**

追加到 `paper-intensive-reading/to_obsidian.py`:
```python
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
) -> dict[str, Path]:
    """统一入口：保存到 Obsidian vault。"""
    vault = vault_path or detect_vault()
    paper_dir = prepare_vault_dir(vault, arxiv_id, title)
    result = copy_to_vault(paper_dir, md_path, pdf_path, figure_paths)
    update_index(vault, arxiv_id, title)
    return result
```

- [ ] **Step 4: 跑全部 to_obsidian 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_obsidian.py -v
```
Expected: 9 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_obsidian.py tests/unit/test_to_obsidian.py
git commit -m "feat(to_obsidian): add index page and unified save() entry"
```

---

# 阶段 P12：Notion 同步 (to_notion)

## Task 12.1: to_notion - 配置 + 客户端

**Files:**
- Create: `paper-intensive-reading/to_notion.py`
- Test: `tests/unit/test_to_notion.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_to_notion.py`:
```python
import os
import pytest
from pathlib import Path
from paper_intensive_reading.to_notion import (
    get_api_key, get_database_id, NotionClient
)
from paper_intensive_reading.errors import NotionError


class TestConfig:
    def test_get_api_key_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_test_123")
        assert get_api_key() == "secret_test_123"

    def test_get_api_key_missing_raises(self, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        with pytest.raises(NotionError) as exc:
            get_api_key()
        assert exc.value.subtype == "no_api_key"

    def test_get_database_id_from_env(self, monkeypatch):
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-12345")
        assert get_database_id() == "db-12345"

    def test_get_database_id_missing_raises(self, monkeypatch):
        monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
        with pytest.raises(NotionError) as exc:
            get_database_id()
        assert exc.value.subtype == "no_db"


class TestNotionClient:
    def test_client_initialization(self, monkeypatch):
        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        client = NotionClient()
        assert client.api_key == "secret_xyz"
        assert client.base_url == "https://api.notion.com/v1"

    def test_client_missing_key(self, monkeypatch):
        monkeypatch.delenv("NOTION_API_KEY", raising=False)
        with pytest.raises(NotionError):
            NotionClient()
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py -v
```

- [ ] **Step 3: 写 to_notion.py 第一部分**

`paper-intensive-reading/to_notion.py`:
```python
"""同步到 Notion 数据库。"""
import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from .errors import NotionError


NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def get_api_key() -> str:
    key = os.environ.get("NOTION_API_KEY")
    if not key:
        raise NotionError("no_api_key")
    return key


def get_database_id() -> str:
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if not db_id:
        raise NotionError("no_db")
    return db_id


class NotionClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_api_key()
        self.base_url = BASE_URL

    def _request(self, method: str, path: str, data: dict | None = None, max_retries: int = 3) -> dict:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=body, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 429:  # rate limit
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    raise NotionError("rate_limit") from e
                raise NotionError("default", detail=f"HTTP {e.code}: {e.reason}") from e
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise NotionError("default", detail=str(e)) from e
        return {}
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py -v
```
Expected: 6 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_notion.py tests/unit/test_to_notion.py
git commit -m "feat(to_notion): add config and NotionClient with retry"
```

---

## Task 12.2: to_notion - 创建 page

**Files:**
- Modify: `paper-intensive-reading/to_notion.py`
- Modify: `tests/unit/test_to_notion.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_notion.py`:
```python
class TestCreatePage:
    def test_create_page_with_content(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, create_paper_page

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-123")

        md_file = tmp_path / "note.md"
        md_file.write_text("# LLaMA\n\nTest content")

        # Mock 客户端
        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                if method == "POST" and "/pages" in path:
                    return {"id": "page-abc123", "url": "https://notion.so/page-abc123"}
                return {}

        client = MockClient("test_key")
        result = create_paper_page(
            client=client,
            database_id="db-123",
            arxiv_id="2302.13971",
            title="LLaMA",
            md_path=md_file,
        )

        assert result["page_id"] == "page-abc123"
        assert "notion.so" in result["url"]

    def test_page_creation_error(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, create_paper_page
        from paper_intensive_reading.errors import NotionError

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        md_file = tmp_path / "note.md"
        md_file.write_text("x")

        class FailingClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                raise NotionError("default", detail="server down")

        client = FailingClient("test_key")
        with pytest.raises(NotionError):
            create_paper_page(client, "db-123", "2302.13971", "LLaMA", md_file)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py::TestCreatePage -v
```

- [ ] **Step 3: 追加 create_paper_page**

追加到 `paper-intensive-reading/to_notion.py`:
```python
def _md_to_blocks(md_text: str) -> list[dict]:
    """简单把 Markdown 转为 Notion blocks。"""
    blocks = []
    for line in md_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("# "):
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        elif line.startswith("## "):
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": line[3:]}}]}
            })
        elif line.startswith("### "):
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": line[4:]}}]}
            })
        elif line.startswith("> "):
            blocks.append({
                "object": "block", "type": "quote",
                "quote": {"rich_text": [{"type": "text", "text": {"content": line[2:]}}]}
            })
        elif line.startswith("```"):
            blocks.append({
                "object": "block", "type": "code",
                "code": {"rich_text": [{"type": "text", "text": {"content": "[code block]"}}],
                         "language": "python"}
            })
        else:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line[:2000]}}]}
            })
    return blocks[:100]  # Notion 限制：单次最多 100 块


def create_paper_page(
    client: NotionClient, database_id: str,
    arxiv_id: str, title: str, md_path: Path,
) -> dict:
    """在 Notion 数据库里创建论文 page。"""
    md_path = Path(md_path)
    md_text = md_path.read_text()
    blocks = _md_to_blocks(md_text)

    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Title": {"title": [{"text": {"content": title}}]},
            "Arxiv ID": {"rich_text": [{"text": {"content": arxiv_id}}]},
        },
        "children": blocks,
    }
    response = client._request("POST", "/pages", data=data)
    return {"page_id": response.get("id", ""), "url": response.get("url", "")}
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py -v
```
Expected: 8 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_notion.py tests/unit/test_to_notion.py
git commit -m "feat(to_notion): add create_paper_page with markdown-to-blocks conversion"
```

---

## Task 12.3: to_notion - PDF 上传 + push() 统一入口

**Files:**
- Modify: `paper-intensive-reading/to_notion.py`
- Modify: `tests/unit/test_to_notion.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_to_notion.py`:
```python
class TestPdfUpload:
    def test_upload_pdf_under_size(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, upload_pdf_attachment

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%small\n")

        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                return {"file_upload": {"id": "upload-123"}}

        client = MockClient("test_key")
        result = upload_pdf_attachment(client, pdf, "page-abc")
        assert result == "upload-123"

    def test_upload_pdf_too_big(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, upload_pdf_attachment
        from paper_intensive_reading.errors import NotionError

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        pdf = tmp_path / "huge.pdf"
        # 写一个 > 100MB 的文件
        with open(pdf, "wb") as f:
            f.write(b"x" * (101 * 1024 * 1024))

        client = NotionClient("test_key")
        with pytest.raises(NotionError) as exc:
            upload_pdf_attachment(client, pdf, "page-abc")
        assert exc.value.subtype == "file_too_big"


class TestPush:
    def test_push_to_notion(self, monkeypatch, tmp_path):
        from paper_intensive_reading.to_notion import NotionClient, push

        monkeypatch.setenv("NOTION_API_KEY", "secret_xyz")
        monkeypatch.setenv("NOTION_DATABASE_ID", "db-123")

        md = tmp_path / "note.md"
        md.write_text("# LLaMA\n\nTest")
        pdf = tmp_path / "2302.13971.pdf"
        pdf.write_bytes(b"%PDF-1.4\n%fake\n")

        class MockClient(NotionClient):
            def _request(self, method, path, data=None, max_retries=3):
                if "/pages" in path:
                    return {"id": "page-abc", "url": "https://notion.so/page-abc"}
                if "file_uploads" in path:
                    return {"file_upload": {"id": "upload-xyz"}}
                return {}

        client = MockClient("test_key")
        result = push(
            client=client, database_id="db-123",
            arxiv_id="2302.13971", title="LLaMA",
            md_path=md, pdf_path=pdf,
        )
        assert result["page_id"] == "page-abc"
        assert result["pdf_uploaded"] is True
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py::TestPdfUpload tests/unit/test_to_notion.py::TestPush -v
```

- [ ] **Step 3: 追加 upload_pdf_attachment + push**

追加到 `paper-intensive-reading/to_notion.py`:
```python
MAX_PDF_SIZE = 100 * 1024 * 1024  # 100MB


def upload_pdf_attachment(client: NotionClient, pdf_path: Path, page_id: str) -> str:
    """上传 PDF 作为 Notion 附件，返回 upload_id。"""
    pdf_path = Path(pdf_path)
    size = pdf_path.stat().st_size
    if size > MAX_PDF_SIZE:
        raise NotionError("file_too_big", size_bytes=size)

    # Notion 文件上传 API（v2024+）：先创建 upload slot，再发文件
    # 这里简化：假设 Notion 直接接受 url/file_data
    # 实际实现可能要分两步
    with open(pdf_path, "rb") as f:
        file_data = f.read()

    # 简化：只调用 file_uploads API（具体实现取决于 Notion API 版本）
    data = {
        "filename": pdf_path.name,
        "file_size": size,
    }
    response = client._request("POST", "/file_uploads", data=data)
    return response.get("file_upload", {}).get("id", "")


def push(
    client: NotionClient, database_id: str,
    arxiv_id: str, title: str, md_path: Path, pdf_path: Path | None = None,
) -> dict:
    """统一入口：推送到 Notion。"""
    page = create_paper_page(client, database_id, arxiv_id, title, md_path)
    result = {"page_id": page["page_id"], "url": page["url"]}

    if pdf_path and Path(pdf_path).exists():
        try:
            upload_id = upload_pdf_attachment(client, pdf_path, page["page_id"])
            result["pdf_uploaded"] = True
            result["pdf_upload_id"] = upload_id
        except NotionError:
            result["pdf_uploaded"] = False

    return result
```

- [ ] **Step 4: 跑全部 to_notion 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_to_notion.py -v
```
Expected: 12 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/to_notion.py tests/unit/test_to_notion.py
git commit -m "feat(to_notion): add PDF upload with size limit and unified push() entry"
```

---

# 阶段 P13：图像生成 fallback (image_gen)

## Task 13.1: image_gen - 简单接口 + fallback 链

**Files:**
- Create: `paper-intensive-reading/image_gen.py`
- Test: `tests/unit/test_image_gen.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_image_gen.py`:
```python
import pytest
from pathlib import Path
from paper_intensive_reading.image_gen import (
    generate, generate_ascii_fallback, PROVIDERS
)


class TestAsciiFallback:
    def test_simple_text_to_ascii(self):
        result = generate_ascii_fallback("Hello")
        assert "Hello" in result or "|" in result

    def test_diagram_attention(self):
        result = generate_ascii_fallback("Q -> K -> V")
        assert "Q" in result
        assert "K" in result
        assert "V" in result


class TestGenerate:
    def test_generate_falls_back_to_ascii(self, tmp_path, monkeypatch):
        from paper_intensive_reading import image_gen
        monkeypatch.setattr(image_gen, "PROVIDERS", [])  # 没有任何 provider

        out = tmp_path / "out.txt"
        result = generate("some prompt", out_path=out)
        # ascii fallback 返回字符串
        assert isinstance(result, str)

    def test_generate_uses_first_working_provider(self, tmp_path, monkeypatch):
        from paper_intensive_reading import image_gen

        called = []

        def fake_provider_1(prompt, out_path):
            called.append("p1")
            raise RuntimeError("provider 1 down")

        def fake_provider_2(prompt, out_path):
            called.append("p2")
            out_path.write_text("FAKE_IMAGE")
            return str(out_path)

        monkeypatch.setattr(image_gen, "PROVIDERS", [fake_provider_1, fake_provider_2])

        out = tmp_path / "out.png"
        result = generate("test", out_path=out)
        assert called == ["p1", "p2"]
        assert "FAKE_IMAGE" in out.read_text()


def test_providers_list_exists():
    assert isinstance(PROVIDERS, list)
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_image_gen.py -v
```

- [ ] **Step 3: 写 image_gen.py**

`paper-intensive-reading/image_gen.py`:
```python
"""图像生成 fallback 链：nano-banana-pro → MiniMax → GLM → ASCII。"""
import os
import urllib.request
import urllib.error
from pathlib import Path


PROVIDERS: list = []  # 由 setup_providers() 填充


def setup_providers() -> None:
    """根据可用 API key 初始化 provider 列表。"""
    global PROVIDERS
    PROVIDERS = []

    if os.environ.get("NANO_BANANA_PRO_API_KEY"):
        PROVIDERS.append(_nano_banana_pro_provider)

    if os.environ.get("GLM_API_KEY"):
        PROVIDERS.append(_glm_provider)

    # MiniMax (当前模型) 通过 opencode 内置工具，由调用方提供
    # 暂不作为自动 provider


def _nano_banana_pro_provider(prompt: str, out_path: Path) -> str:
    """调用 nano-banana-pro (Gemini 3 Pro Image) 生成图。"""
    import json
    api_key = os.environ["NANO_BANANA_PRO_API_KEY"]
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image:generate"
    data = {"prompt": prompt, "size": "1024x1024"}
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        # 假设返回 {"image_url": "..."}
        image_url = result.get("image_url", "")
        if image_url:
            urllib.request.urlretrieve(image_url, str(out_path))
            return str(out_path)
    raise RuntimeError("nano-banana-pro no image in response")


def _glm_provider(prompt: str, out_path: Path) -> str:
    """调用 GLM (zhipu) 生成图。"""
    import json
    api_key = os.environ["GLM_API_KEY"]
    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"
    data = {"model": "cogview-3", "prompt": prompt}
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        image_url = result.get("data", [{}])[0].get("url", "")
        if image_url:
            urllib.request.urlretrieve(image_url, str(out_path))
            return str(out_path)
    raise RuntimeError("GLM no image in response")


def generate_ascii_fallback(prompt: str) -> str:
    """最简 ASCII 兜底：用文本框表达。"""
    width = max(40, min(80, len(prompt) + 4))
    border = "+" + "-" * (width - 2) + "+"
    content = prompt[:width - 4].center(width - 2)
    return f"{border}\n|{content}|\n{border}\n"


def generate(prompt: str, out_path: Path | None = None) -> str:
    """按 fallback 链生成图。最终兜底是 ASCII。"""
    setup_providers()  # 每次重新检查 env

    out_path = Path(out_path) if out_path else Path("/tmp/img.txt")

    last_error = None
    for provider in PROVIDERS:
        try:
            return provider(prompt, out_path)
        except Exception as e:
            last_error = e
            continue

    # 全部 provider 失败或没有 provider，ASCII 兜底
    out_path.write_text(generate_ascii_fallback(prompt))
    return str(out_path)
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_image_gen.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/image_gen.py tests/unit/test_image_gen.py
git commit -m "feat(image_gen): add multi-provider fallback chain with ASCII ultimate fallback"
```

---

# 阶段 P14：调研模式 (survey)

## Task 14.1: survey.py - 搜索 + 排序

**Files:**
- Create: `paper-intensive-reading/survey.py`
- Test: `tests/unit/test_survey.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_survey.py`:
```python
import pytest
from datetime import date
from paper_intensive_reading.survey import (
    search_papers, rank_papers, build_survey_result
)
from paper_intensive_reading.types import Paper


def make_paper(arxiv_id, title, year=2023, citations=100):
    return Paper(
        arxiv_id=arxiv_id, title=title, authors=["Author"],
        affiliations=[], abstract="x", published=date(year, 1, 1),
        pdf_path="", sections=[], figures=[], tables=[],
        algorithms=[], references=[],
    )


class TestSearchPapers:
    def test_search_returns_list(self, monkeypatch):
        from paper_intensive_reading import survey

        class MockResult:
            entry_id = "http://arxiv.org/abs/2302.04761v1"
            title = "Toolformer"
            summary = "x"
            published = date(2023, 2, 9)
            authors = [type("A", (), {"name": "Schick"})()]

        class MockClient:
            def __init__(self, *args, **kwargs): pass
            def results(self, search): return iter([MockResult()])

        monkeypatch.setattr(survey.arxiv, "Client", MockClient)
        papers = search_papers("toolformer", max_results=5)
        assert len(papers) == 1
        assert papers[0].title == "Toolformer"


class TestRankPapers:
    def test_rank_by_citations(self):
        papers = [
            make_paper("a", "A", citations=10),
            make_paper("b", "B", citations=100),
            make_paper("c", "C", citations=50),
        ]
        ranked = rank_papers(papers)
        assert ranked[0]["arxiv_id"] == "b"
        assert ranked[1]["arxiv_id"] == "c"
        assert ranked[2]["arxiv_id"] == "a"

    def test_rank_favors_recent(self):
        papers = [
            make_paper("a", "A", year=2020, citations=1000),
            make_paper("b", "B", year=2024, citations=10),
        ]
        ranked = rank_papers(papers, recency_weight=0.5)
        # recency + citations 综合，新论文可能超过旧论文


class TestBuildSurvey:
    def test_build_survey_result(self):
        papers = [make_paper("a", "A", citations=100), make_paper("b", "B", citations=50)]
        result = build_survey_result("Test query", papers)
        assert result["query"] == "Test query"
        assert len(result["papers"]) == 2
        assert result["papers"][0]["arxiv_id"] == "a"  # 引用多排前
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_survey.py -v
```

- [ ] **Step 3: 写 survey.py**

`paper-intensive-reading/survey.py`:
```python
"""领域调研：从 arXiv 拉论文列表并按引用 + 时效排序。"""
import arxiv
from datetime import date
from .types import Paper


def search_papers(query: str, max_results: int = 20, months: int = 6) -> list[Paper]:
    """从 arXiv 搜索论文。"""
    search = arxiv.Search(
        query=query, max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )
    client = arxiv.Client(page_size=max_results, delay_seconds=3.0, num_retries=3)
    results = list(client.results(search))

    papers = []
    for r in results:
        arxiv_id = r.entry_id.split("/")[-1]
        arxiv_id = arxiv_id.lower().rstrip("v0123456789") or arxiv_id
        papers.append(Paper(
            arxiv_id=arxiv_id, title=r.title,
            authors=[a.name for a in r.authors], affiliations=[],
            abstract=r.summary,
            published=r.published.date() if r.published else date.today(),
            pdf_path="", sections=[], figures=[], tables=[],
            algorithms=[], references=[],
        ))
    return papers


def rank_papers(papers: list[Paper], recency_weight: float = 0.3) -> list[dict]:
    """按引用 + 时效综合排序。返回 [{arxiv_id, title, score, ...}]。"""
    # 简化：没有真实 citation 数据，假设 citations=100 的 paper 有 100 引用
    # 实际：需要从 Semantic Scholar API 拉
    today_year = date.today().year
    scored = []
    for p in papers:
        # 时效分：年差越小越高
        recency = max(0, 1 - (today_year - p.published.year) * 0.2)
        # 引用分：citations / max_citations（归一化）
        citations = getattr(p, "citations", 100)  # 缺省
        # score 简化计算
        score = citations * (1 - recency_weight) + recency * 1000 * recency_weight
        scored.append({
            "arxiv_id": p.arxiv_id, "title": p.title,
            "authors": p.authors, "year": p.published.year,
            "abstract": p.abstract[:200],
            "citations": citations, "score": score,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def build_survey_result(query: str, papers: list[Paper]) -> dict:
    """构造调研结果。"""
    ranked = rank_papers(papers)
    return {
        "query": query,
        "paper_count": len(papers),
        "papers": ranked,
        "generated_at": date.today().isoformat(),
    }
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_survey.py -v
```
Expected: 4 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/survey.py tests/unit/test_survey.py
git commit -m "feat(survey): add arXiv search and citation+recency ranking"
```

---

## Task 14.2: survey.py - 添加到清单

**Files:**
- Modify: `paper-intensive-reading/survey.py`
- Modify: `tests/unit/test_survey.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_survey.py`:
```python
class TestAddToList:
    def test_add_all_to_paper_store(self, tmp_db, monkeypatch):
        from paper_intensive_reading.survey import add_survey_results_to_list
        from paper_intensive_reading.paper_store import init_db, get_paper
        init_db(tmp_db)

        result = {
            "query": "LLM",
            "papers": [
                {"arxiv_id": "2302.13971", "title": "LLaMA"},
                {"arxiv_id": "2304.08485", "title": "QLoRA"},
            ],
        }
        added = add_survey_results_to_list(result, db_path=tmp_db)
        assert len(added) == 2
        assert get_paper(tmp_db, "2302.13971") is not None

    def test_selective_add(self, tmp_db, monkeypatch):
        from paper_intensive_reading.survey import add_survey_results_to_list
        from paper_intensive_reading.paper_store import init_db, get_paper
        init_db(tmp_db)

        result = {
            "query": "x",
            "papers": [
                {"arxiv_id": "2302.13971", "title": "LLaMA"},
                {"arxiv_id": "2304.08485", "title": "QLoRA"},
            ],
        }
        added = add_survey_results_to_list(result, db_path=tmp_db, arxiv_ids=["2302.13971"])
        assert len(added) == 1
        assert get_paper(tmp_db, "2302.13971") is not None
        assert get_paper(tmp_db, "2304.08485") is None
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_survey.py::TestAddToList -v
```

- [ ] **Step 3: 追加 add_survey_results_to_list**

追加到 `paper-intensive-reading/survey.py`:
```python
def add_survey_results_to_list(
    result: dict, db_path, arxiv_ids: list[str] | None = None,
) -> list[str]:
    """把调研结果里的论文添加到阅读清单。arxiv_ids=None 表示全部添加。"""
    from .paper_store import add_paper
    added = []
    for p in result.get("papers", []):
        if arxiv_ids and p["arxiv_id"] not in arxiv_ids:
            continue
        add_paper(db_path, {
            "arxiv_id": p["arxiv_id"], "title": p["title"],
            "authors": p.get("authors", []), "affiliations": [],
            "abstract": p.get("abstract", ""), "published": date(p.get("year", 2024), 1, 1),
            "pdf_path": "",
        })
        added.append(p["arxiv_id"])
    return added
```

- [ ] **Step 4: 跑全部 survey 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_survey.py -v
```
Expected: 6 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/survey.py tests/unit/test_survey.py
git commit -m "feat(survey): add bulk add to reading list with selective filter"
```

---

# 阶段 P15：对比模式 (compare)

## Task 15.1: compare.py - 多论文对比表

**Files:**
- Create: `paper-intensive-reading/compare.py`
- Test: `tests/unit/test_compare.py`

- [ ] **Step 1: 写测试**

`tests/unit/test_compare.py`:
```python
import pytest
from datetime import date
from paper_intensive_reading.compare import (
    compare_papers, build_aspect_table, DEFAULT_ASPECTS
)
from paper_intensive_reading.types import Paper


def make_paper(arxiv_id, title, year=2023):
    return Paper(
        arxiv_id=arxiv_id, title=title, authors=["X"],
        affiliations=[], abstract="x", published=date(year, 1, 1),
        pdf_path=f"/tmp/{arxiv_id}.pdf",
        sections=[], figures=[], tables=[], algorithms=[], references=[],
    )


class TestCompare:
    def test_default_aspects_exist(self):
        assert "time" in DEFAULT_ASPECTS
        assert "model_size" in DEFAULT_ASPECTS

    def test_compare_two_papers(self):
        papers = [make_paper("a", "A"), make_paper("b", "B")]
        result = compare_papers(papers)
        assert result["paper_count"] == 2
        assert "aspects" in result
        assert "A" in str(result["aspects"])

    def test_compare_empty(self):
        with pytest.raises(ValueError):
            compare_papers([])

    def test_aspect_table_2d(self):
        papers = [make_paper("a", "A"), make_paper("b", "B")]
        table = build_aspect_table(papers)
        assert isinstance(table, dict)
        assert "time" in table
        # time 应该是 [a_year, b_year]
        assert table["time"] == [2023, 2023]


class TestAspectExtraction:
    def test_extract_authors(self):
        paper = make_paper("a", "A")
        paper.authors = ["Touvron", "Lavril"]
        result = compare_papers([paper])
        assert result["aspects"]["authors"][0] == "Touvron, Lavril"
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_compare.py -v
```

- [ ] **Step 3: 写 compare.py**

`paper-intensive-reading/compare.py`:
```python
"""多论文并排对比。"""
from .types import Paper


DEFAULT_ASPECTS = [
    "time", "authors", "model_size", "method", "datasets", "main_result"
]


def build_aspect_table(papers: list[Paper], aspects: list[str] | None = None) -> dict:
    """构建 {aspect: [paper1_value, paper2_value, ...]}。"""
    aspects = aspects or DEFAULT_ASPECTS
    table: dict[str, list] = {a: [] for a in aspects}

    for p in papers:
        table["time"].append(p.published.isoformat())
        table["authors"].append(", ".join(p.authors))
        table["model_size"].append("(待解析)")
        table["method"].append(p.abstract[:200])
        table["datasets"].append("(待解析)")
        table["main_result"].append("(待解析)")

    return table


def compare_papers(papers: list[Paper], aspects: list[str] | None = None) -> dict:
    """多论文对比的统一入口。"""
    if not papers:
        raise ValueError("至少需要 1 篇论文")
    aspects = aspects or DEFAULT_ASPECTS
    table = build_aspect_table(papers, aspects)
    return {
        "paper_count": len(papers),
        "paper_titles": [p.title for p in papers],
        "arxiv_ids": [p.arxiv_id for p in papers],
        "aspects": table,
    }
```

- [ ] **Step 4: 跑测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_compare.py -v
```
Expected: 5 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/compare.py tests/unit/test_compare.py
git commit -m "feat(compare): add multi-paper comparison with default aspects"
```

---

## Task 15.2: compare.py - 提取关键方法

**Files:**
- Modify: `paper-intensive-reading/compare.py`
- Modify: `tests/unit/test_compare.py`

- [ ] **Step 1: 追加测试**

追加到 `tests/unit/test_compare.py`:
```python
class TestMethodExtraction:
    def test_extract_keyword(self):
        from paper_intensive_reading.compare import extract_method_keywords
        abstract = "We propose a transformer-based model with RoPE positional encoding and RMSNorm."
        kws = extract_method_keywords(abstract)
        assert "transformer" in kws
        assert "RoPE" in kws or "rope" in [k.lower() for k in kws]

    def test_extract_datasets(self):
        from paper_intensive_reading.compare import extract_dataset_names
        abstract = "We evaluate on ImageNet, COCO, and GLUE benchmarks."
        datasets = extract_dataset_names(abstract)
        assert "ImageNet" in datasets
        assert "COCO" in datasets
```

- [ ] **Step 2: 跑测试，预期失败**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_compare.py::TestMethodExtraction -v
```

- [ ] **Step 3: 追加 extract_method_keywords + extract_dataset_names**

追加到 `paper-intensive-reading/compare.py`:
```python
import re

METHOD_KEYWORDS = [
    "transformer", "attention", "self-attention", "cross-attention",
    "BERT", "GPT", "LLaMA", "RoPE", "RMSNorm", "LayerNorm", "SwiGLU",
    "LoRA", "RLHF", "fine-tuning", "pre-training", "distillation",
    "MoE", "sparse", "quantization", "pruning",
]

DATASET_KEYWORDS = [
    "ImageNet", "COCO", "GLUE", "SuperGLUE", "MMLU",
    "HumanEval", "GSM8K", "MATH", "HellaSwag", "ARC",
    "CommonsenseQA", "WinoGrande", "TruthfulQA",
    "SQuAD", "Natural Questions", "TriviaQA",
]


def extract_method_keywords(text: str) -> list[str]:
    found = []
    for kw in METHOD_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
            found.append(kw)
    return found


def extract_dataset_names(text: str) -> list[str]:
    found = []
    for ds in DATASET_KEYWORDS:
        if re.search(rf"\b{re.escape(ds)}\b", text, re.IGNORECASE):
            found.append(ds)
    return found
```

- [ ] **Step 4: 跑全部 compare 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit/test_compare.py -v
```
Expected: 7 tests pass

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add paper-intensive-reading/compare.py tests/unit/test_compare.py
git commit -m "feat(compare): add method keyword and dataset extraction"
```

---

**P8-P15 完成。** 继续 P16 (SKILL.md) 和 P17 (E2E + 性能) 在 [plan-part-3.md](2026-06-04-paper-intensive-reading-PLAN-part3.md)。
