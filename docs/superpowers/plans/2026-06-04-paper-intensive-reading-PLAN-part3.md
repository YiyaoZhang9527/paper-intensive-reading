# 论文精读 Skill 实施计划 (Part 3: P16-P17)

> 接 [plan-part-1.md](2026-06-04-paper-intensive-reading-PLAN.md) 和 [plan-part-2.md](2026-06-04-paper-intensive-reading-PLAN-part2.md)，覆盖 P16 SKILL.md 主入口、P17 端到端 + 性能 + 安全 + 收尾。

---

# 阶段 P16：主入口 SKILL.md

## Task 16.1: SKILL.md - 对话剧本核心

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: 写 SKILL.md**

`SKILL.md`:
```markdown
---
name: paper-intensive-reading
description: 对话式 AI/ML 论文精读。从 arXiv 下载 PDF，用小学数学基础讲解每个公式（带 NumPy 实际运行 + 三对照验证），强制做理解确认循环，沉淀笔记到本地 MD / Obsidian / Notion 三端。
triggers:
  - /paper-read
  - /paper-list
  - /paper-survey
  - 论文精读
  - 帮我读论文
  - 精读这篇论文
---

# Paper Intensive Reading Skill

## 触发方式

- `/paper-read <id>` — 单篇精读（如 `/paper-read 2302.13971`）
- `/paper-read --compare <id1> <id2>` — 多篇对比
- `/paper-list` — 查看阅读清单
- `/paper-list --add <id>` — 添加到清单
- `/paper-survey "<query>"` — 领域调研
- `/paper-errors` — 查看错误日志

输入支持：arXiv ID、URL、本地 PDF 路径、标题搜索、BibTeX。

## 核心规则（必须遵守）

### 1. 公式讲解 6 段结构
每个公式必须输出 6 段，缺一不可：
1. **原始形式**（LaTeX）
2. **白话翻译**（一句中文，不超过 30 字）
3. **逐符号解释**（带阶梯层号）
4. **直觉类比**（生活场景）
5. **详细计算示例**（d=2 或 d=4 极小例子）
6. **NumPy 代码 + 实际运行结果**（手算 = 代码 = 跑出 三对照）

### 2. 理解确认循环
每讲完一个公式，强制要求用户回答 3 个验证问题中的 1 个：
- "这个公式在算什么？"
- "例子里的第 X 步，对应公式的哪个符号？"
- "如果某个参数变化，结果怎么变？"

**拒绝"我不懂"、"我懂了但说不出来"** — 必须具体指出哪里不懂。

### 3. 数学基础预设
默认预设用户数学只有小学水平。从 math-ladder.md 的第 0 层（算术）开始讲，遇到公式自动查阶梯决定起点。

### 4. 对话节奏硬约束
- 每节讲解不超过 800 字
- 每个公式都跟一段白话
- 每完成一节必问一次反馈
- 每 3 节提醒一次保存

### 5. 多端同步
笔记生成后默认同步到：本地 MD、Obsidian（如果配置）、Notion（如果配置）。
PDF 同步存储（不只存笔记）。

## 工作流程

### 标准开场
```
Skill: 收到！我来下载并解析这篇论文……

       📄 LLaMA: Open and Efficient Foundation Language Models
       👥 Touvron et al., Meta AI, 2023
       🔗 arXiv:2302.13971
       
       ⏱ 正在解析 PDF 结构和图表…（约 30 秒）

       ✅ 解析完成。我识别出：
       - 6 个主章节
       - 12 个关键公式
       - 5 个算法伪代码
       - 8 张图表
       
       你希望用哪种模式开始？
       1) 章节引导（推荐）：我带你一节一节读
       2) 关键点专讲：聚焦 3-5 个核心创新点
       3) 自由模式：你自己点哪节我讲哪节
       
       预设你的数学基础为「小学」，我会从最基础的算术开始讲每个公式。
```

### 章节引导循环（每节 4 步）
1. 推送本节内容（白话 + 要点 + 公式 + 图表）
2. 自适应难度检查
3. 进度 + 决定
4. 用户随时可插入：追问、举例、跳节、保存

### 关键点专讲模式
通读后标出 3-5 个最值得深入的创新点，逐个重点讲。

### 阅读清单模式
- `/paper-list` — 显示待读/在读/已读完清单
- `/paper-list --add <id>` — 添加
- `/paper-list --status in-progress` — 筛选

### 调研模式
`/paper-survey "<query>"` → 拉 Top 10 论文 → 用户选添加。

## 错误处理

任何错误都用中文友好消息（不抛原始异常）：
- `arxiv_404` → "arXiv 上找不到这篇论文（ID: xxx）..."
- `parse_dangerous` → "PDF 包含可执行动作（JavaScript/宏）..."
- `numpy_timeout` → "代码运行超过 10 秒..."
- `obsidian_no_vault` → "找不到 Obsidian vault..."

完整消息见 `paper-intensive-reading/errors.py` 的 `get_user_message()`。

## 降级策略

| 失败点 | 降级方案 |
|-------|---------|
| 公式图片生成失败 | 保留 LaTeX + ASCII 艺术 |
| 公式代码运行失败 | 保留手算例子，省略第 6 段 |
| 图表提取失败 | 保留 PDF 链接 + 文字描述 |
| Obsidian 失败 | 仅本地保存 + 警告 |
| Notion 失败 | 本地 + Obsidian + 警告 |
| LLM 限流 | 排队 30 秒 |

## 调用关系

详细见 [PLAN.md §2.2](../../plans/2026-06-04-paper-intensive-reading-PLAN.md)。

## 参考资料

- 设计文档：`docs/superpowers/specs/2026-06-04-paper-intensive-reading-design.md`
- 实施计划：`docs/superpowers/plans/2026-06-04-paper-intensive-reading-PLAN*.md`
- 数学阶梯：`references/math-ladder.md`
- 公式术语：`paper-intensive-reading/bilingual.py`
```

- [ ] **Step 2: 验证文件存在**

```bash
cd /Users/zhangjing/Documents/论文精度
ls -la SKILL.md
wc -l SKILL.md
```

- [ ] **Step 3: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add SKILL.md
git commit -m "docs(skill): add main SKILL.md with conversation script, hard rules, and error handling"
```

---

## Task 16.2: SKILL.md - 引用文档

**Files:**
- Create: `references/paper-templates.md`
- Create: `references/image-providers.md`
- Create: `references/ai-ml-concepts.md`（占位）
- Create: `references/formula-glossary.md`（占位）

- [ ] **Step 1: 写 paper-templates.md**

`references/paper-templates.md`:
```markdown
# 精读笔记模板

## 模板 1：单篇精读（默认）

\`\`\`markdown
---
arxiv_id: 2302.13971
title: "LLaMA: Open and Efficient Foundation Language Models"
authors: [Touvron, Lavril]
year: 2023
status: 已读完
tags: [llm, foundation-model, pretraining]
depth_pref: elementary
---

# LLaMA: ...

> **TL;DR**：[一句话]

## 1. 背景与动机
## 2. 核心贡献
## 3. 方法详解
### 3.1 [小节]
#### 公式 (1)：[公式名]
[6 段讲解]
## 4. 实验与结果
## 5. 讨论与启示
## 6. 术语表
## 7. 参考资料
\`\`\`

## 模板 2：多篇对比

\`\`\`markdown
---
mode: compare
papers: 2
---

# 对比：A vs B

## 概览对比
| 维度 | A | B |
| ... | ... | ... |

## 关键方法对比
## 实验对比
## 借鉴决策
\`\`\`

## 模板 3：领域调研

\`\`\`markdown
---
mode: survey
query: "LLM Agents"
---

# 调研：LLM Agents

## 1. Toolformer
**为什么读**：...
**核心方法**：...
**arXiv**：[link]

## 2. ReAct
...

## 阅读路径建议
\`\`\`
```

- [ ] **Step 2: 写 image-providers.md**

`references/image-providers.md`:
```markdown
# 图像生成 Provider 配置

按 fallback 链顺序尝试：

1. **nano-banana-pro** (Gemini 3 Pro Image)
   - 环境变量：`NANO_BANANA_PRO_API_KEY`
   - URL: `https://generativelanguage.googleapis.com/v1beta/...`

2. **MiniMax-M3** (当前模型)
   - 通过 opencode 内置工具调用
   - 可生成 SVG / Mermaid / matplotlib 输出

3. **GLM** (zhipu cogview-3)
   - 环境变量：`GLM_API_KEY`
   - URL: `https://open.bigmodel.cn/api/paas/v4/...`

4. **ASCII 兜底**
   - 任何 provider 都失败时使用纯文本框

## 配置

在 `~/.zshrc` 或项目 `.env` 中设置：

\`\`\`bash
export NANO_BANANA_PRO_API_KEY="..."
export GLM_API_KEY="..."
\`\`\`

skill 会自动检测哪些 provider 可用。
```

- [ ] **Step 3: 写 ai-ml-concepts.md 占位**

`references/ai-ml-concepts.md`:
```markdown
# AI/ML 零基础概念库

> 给 AI 用的"AI 概念白话解释"参考。当用户问"什么是 X"时，从这里取解释。

## 神经网络基础
- 神经元：人脑神经细胞的数学模拟
- 神经网络：很多神经元按层连接
- 深度学习："深"指隐藏层多
- 反向传播：从输出层向输入层，逐层计算梯度
- 梯度下降：找函数最小值的方法

## Transformer 架构
- Transformer：基于自注意力的架构
- 自注意力：序列中每个位置看其他位置
- Q/K/V：Query/Key/Value 三个角色
- 多头注意力：并行多组 Q/K/V
- 位置编码：让模型感知序列位置

（详细定义在实施 P7 阶段可补充）
```

- [ ] **Step 4: 写 formula-glossary.md 占位**

`references/formula-glossary.md`:
```markdown
# 公式符号对照表

> 常见公式符号的中英文对照和概念层归属。

## 矩阵运算
| 符号 | 含义 | 阶梯层 |
|------|------|--------|
| $A$, $B$, $C$ | 矩阵 | 5 |
| $x$, $y$, $z$ | 向量 | 5 |
| $A^\top$ | 转置 | 5 |
| $A^{-1}$ | 逆矩阵 | 5 |
| $A \cdot B$ 或 $AB$ | 矩阵乘法 | 5 |
| $x^\top y$ 或 $\langle x, y \rangle$ | 内积 / 点积 | 5 |

## 注意力
| 符号 | 含义 | 阶梯层 |
|------|------|--------|
| $Q$ | Query（查询向量） | 5 |
| $K$ | Key（键向量） | 5 |
| $V$ | Value（值向量） | 5 |
| $d_k$ | Key 的维度 | 5 |
| $\text{softmax}$ | 归一化为概率 | 4 |
| $\sqrt{d_k}$ | 缩放因子 | 0 |

（更多符号在实施过程中补充）
```

- [ ] **Step 5: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add references/paper-templates.md references/image-providers.md references/ai-ml-concepts.md references/formula-glossary.md
git commit -m "docs(references): add paper templates, image providers config, AI/ML concepts placeholder, formula glossary"
```

---

# 阶段 P17：端到端 + 性能 + 安全 + 收尾

## Task 17.1: 端到端测试 - LLaMA 论文

**Files:**
- Create: `tests/e2e/test_full_llama_read.py`
- Create: `tests/e2e/__init__.py`

- [ ] **Step 1: 写 E2E 测试（mock LLM 避免实际调用）**

`tests/e2e/test_full_llama_read.py`:
```python
"""端到端测试：完整跑一篇论文的精读流程。

注意：使用 mock LLM 避免实际 API 调用。
真正的 E2E（实际下载 LLaMA PDF）作为可选 manual test。
"""
import os
import pytest
from pathlib import Path
from datetime import date
from unittest.mock import patch

from paper_intensive_reading.types import Paper
from paper_intensive_reading.pdf_parse import parse
from paper_intensive_reading.to_markdown import render_single_note
from paper_intensive_reading.formula_explainer import (
    FormulaExplanation, FormulaSegment, build_empty_explanation
)
from paper_intensive_reading.paper_store import (
    init_db, add_paper, get_paper, update_status
)


@pytest.fixture
def sample_paper_with_pdf(tmp_path):
    """构造一个带 PDF 文件的 Paper 对象（用 PyMuPDF 生成）。"""
    import fitz
    pdf_path = tmp_path / "2302.13971.pdf"
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "LLaMA: Open and Efficient Foundation Language Models")
    doc.new_page().insert_text(
        (50, 50),
        "Abstract\nWe introduce LLaMA, a collection of foundation models.\n\n"
        "1 Introduction\n\nFoundation models are large language models.\n\n"
        "2 Method\n\nWe use RMSNorm. Eq. (1): x = y + z.\n\n"
        "3 Experiments\n\nResults on benchmarks.\n\n"
        "Figure 1: Architecture diagram.",
    )
    doc.save(str(pdf_path))
    doc.close()

    return pdf_path


def test_full_pipeline_parse_to_note(tmp_path, sample_paper_with_pdf):
    """完整流程：PDF → Paper → 公式讲解 → Markdown。"""
    # 1. 解析 PDF
    paper = parse(sample_paper_with_pdf)
    paper.arxiv_id = "2302.13971"
    paper.published = date(2023, 2, 27)
    assert "LLaMA" in paper.title
    assert len(paper.sections) >= 1

    # 2. 构造一个 mock 公式讲解
    expl = build_empty_explanation()
    expl.arxiv_id = "2302.13971"
    expl.formula_number = "(1)"
    expl.latex = "x = y + z"
    expl.segments[1] = FormulaSegment(kind="plain", content="x 等于 y 加 z")
    expl.verified = True
    expl.verification_outputs = {
        "actual": {"ok": True, "stdout": "6"}
    }

    # 把公式归到第一个有公式的 section
    if paper.sections:
        paper.sections[0].formulas.append(
            __import__("paper_intensive_reading.types", fromlist=["Formula"]).Formula(
                number="(1)", latex="x = y + z",
                context_before="", context_after="",
            )
        )

    # 3. 渲染笔记
    user_state = {"depth_pref": "elementary"}
    md = render_single_note(paper, [expl], user_state)

    # 4. 验证产物
    assert "arxiv_id: 2302.13971" in md
    assert "LLaMA" in md
    assert "x 等于 y 加 z" in md
    assert "actual" in md.lower() or "6" in md


def test_full_pipeline_with_db_persistence(tmp_path, sample_paper_with_pdf):
    """测试 SQLite 持久化。"""
    db_path = tmp_path / "papers.sqlite"
    init_db(db_path)

    # add_paper
    add_paper(db_path, {
        "arxiv_id": "2302.13971", "title": "LLaMA",
        "authors": ["Touvron"], "affiliations": ["Meta AI"],
        "abstract": "x", "published": date(2023, 2, 27),
        "pdf_path": str(sample_paper_with_pdf),
    })

    # get_paper
    p = get_paper(db_path, "2302.13971")
    assert p is not None
    assert p["title"] == "LLaMA"
    assert p["status"] == "待读"

    # update_status
    update_status(db_path, "2302.13971", "已读完")
    p2 = get_paper(db_path, "2302.13971")
    assert p2["status"] == "已读完"
    assert p2["finished_at"] is not None
```

- [ ] **Step 2: 写 tests/e2e/__init__.py**

```bash
cd /Users/zhangjing/Documents/论文精度
touch tests/e2e/__init__.py
```

- [ ] **Step 3: 跑 E2E 测试，预期通过**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/e2e -v
```
Expected: 2 tests pass

- [ ] **Step 4: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add tests/e2e/
git commit -m "test(e2e): add full pipeline test (PDF -> Paper -> formula -> Markdown -> DB)"
```

---

## Task 17.2: 性能基准测试

**Files:**
- Create: `tests/performance/test_benchmarks.py`
- Create: `tests/performance/__init__.py`

- [ ] **Step 1: 写基准测试**

`tests/performance/test_benchmarks.py`:
```python
"""性能基准：确保关键操作在合理时间内完成。"""
import time
import fitz
import pytest
from pathlib import Path
from paper_intensive_reading.pdf_parse import parse
from paper_intensive_reading.extract_figures import extract_embedded_images
from paper_intensive_reading.render_formula import render
from paper_intensive_reading.numpy_runner import run


@pytest.fixture
def synthetic_pdf(tmp_path):
    """构造一个 10 页的测试 PDF。"""
    pdf = tmp_path / "test.pdf"
    doc = fitz.open()
    for i in range(10):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i+1}\n\nContent of page {i+1}.")
    doc.save(str(pdf))
    doc.close()
    return pdf


def test_parse_under_5s(synthetic_pdf):
    start = time.time()
    parse(synthetic_pdf)
    duration = time.time() - start
    assert duration < 5, f"parse() took {duration:.2f}s, expected < 5s"


def test_extract_figures_under_10s(synthetic_pdf, tmp_path):
    out_dir = tmp_path / "figs"
    start = time.time()
    extract_embedded_images(synthetic_pdf, out_dir)
    duration = time.time() - start
    assert duration < 10, f"extract took {duration:.2f}s, expected < 10s"


def test_render_formula_under_1s(tmp_path):
    out = tmp_path / "eq.png"
    start = time.time()
    render(r"\frac{a}{b}", out_path=out)
    duration = time.time() - start
    assert duration < 1, f"render took {duration:.2f}s, expected < 1s"


def test_numpy_run_under_5s():
    code = """
import numpy as np
x = np.random.rand(100, 100)
y = x @ x.T
print(y.shape)
"""
    start = time.time()
    result = run(code, timeout=5)
    duration = time.time() - start
    assert result.ok
    assert duration < 5, f"numpy run took {duration:.2f}s, expected < 5s"


@pytest.mark.slow
def test_full_pipeline_under_3min(synthetic_pdf):
    """完整跑一篇论文（10 页）应在 3 分钟内。"""
    from paper_intensive_reading.formula_explainer import build_empty_explanation
    from paper_intensive_reading.to_markdown import render_single_note

    start = time.time()
    paper = parse(synthetic_pdf)
    expl = build_empty_explanation()
    expl.formula_number = "(1)"
    expl.latex = "x = 1"
    md = render_single_note(paper, [expl], {"depth_pref": "elementary"})
    duration = time.time() - start

    assert duration < 180, f"Full pipeline took {duration:.2f}s, expected < 180s"
    assert len(md) > 0
```

- [ ] **Step 2: 写 __init__.py**

```bash
cd /Users/zhangjing/Documents/论文精度
touch tests/performance/__init__.py
```

- [ ] **Step 3: 跑基准测试（跳过 slow）**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/performance -v -m "not slow"
```

- [ ] **Step 4: 提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add tests/performance/
git commit -m "test(performance): add benchmarks for parse, extract, render, numpy_run, full pipeline"
```

---

## Task 17.3: 覆盖率检查 + 收尾

**Files:**
- Modify: `pyproject.toml`（已存在）
- 各种 README

- [ ] **Step 1: 跑全量测试，检查通过率**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/ -v -m "not slow" 2>&1 | tail -50
```

Expected: 大部分测试通过，记录失败的并修复。

- [ ] **Step 2: 跑覆盖率检查**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit tests/integration --cov=paper-intensive-reading --cov-report=term-missing
```

目标：行覆盖 ≥ 80%。

- [ ] **Step 3: 写 README 完整版**

更新 `README.md`:
```markdown
# Paper Intensive Reading Skill

对话式 AI/ML 论文精读 skill。

## 功能

- 从 arXiv 自动下载 PDF（支持 arXiv ID / URL / 标题 / BibTeX / 本地路径）
- 用**小学数学基础**讲解每个公式（带 NumPy 实际运行 + 三对照验证）
- 强制做**理解确认循环**，拒绝"模糊不懂"
- 沉淀笔记到本地 Markdown / Obsidian / Notion 三端
- 4 种模式：单篇精读 / 多篇对比 / 阅读清单 / 领域调研

## 安装

\`\`\`bash
uv sync
\`\`\`

## 使用

详见 [SKILL.md](../SKILL.md) 里的触发方式和对话流程。

## 项目结构

\`\`\`
paper-intensive-reading/   # Python 包
├── types.py              # 数据模型
├── errors.py             # 错误体系
├── arxiv_fetch.py        # 论文获取
├── pdf_parse.py          # PDF 解析
├── extract_figures.py    # 图表提取
├── render_formula.py     # 公式渲染
├── numpy_runner.py       # NumPy 沙箱
├── formula_explainer.py  # 6 段公式讲解
├── math_ladder.py        # 数学概念阶梯
├── bilingual.py          # 中英术语
├── paper_store.py        # 阅读清单
├── to_markdown.py        # 笔记渲染
├── to_obsidian.py        # Obsidian 同步
├── to_notion.py          # Notion 同步
├── image_gen.py          # 图像生成
├── survey.py             # 调研模式
└── compare.py            # 对比模式

references/               # AI 参考资料
├── math-ladder.md        # 数学概念阶梯
├── paper-templates.md    # 笔记模板
├── image-providers.md    # 图像生成配置
├── ai-ml-concepts.md     # 零基础概念
└── formula-glossary.md   # 公式符号对照

tests/                    # 测试
├── unit/                 # 单元测试
├── integration/          # 集成测试
├── e2e/                  # 端到端
├── performance/          # 性能基准
├── safety/               # 沙箱绕过
├── snapshots/            # 快照测试
└── fixtures/             # 测试数据

data/                     # 用户资产
├── papers/pdfs/          # PDF 缓存
├── papers/notes/         # 精读笔记
└── reading-list.sqlite   # 阅读清单
\`\`\`

## 测试

\`\`\`bash
# 全部测试
uv run pytest tests/

# 单元测试
uv run pytest tests/unit

# 性能测试
uv run pytest tests/performance

# 安全测试（沙箱）
uv run pytest tests/safety

# 覆盖率
uv run pytest --cov=paper-intensive-reading --cov-report=html
\`\`\`

## 配置

环境变量（可选）：

- `OBSIDIAN_VAULT_PATH` — Obsidian vault 路径
- `NOTION_API_KEY` — Notion API key
- `NOTION_DATABASE_ID` — Notion 数据库 ID
- `NANO_BANANA_PRO_API_KEY` — Gemini 图像生成 key
- `GLM_API_KEY` — GLM 图像生成 key

## 文档

- [设计文档](docs/superpowers/specs/2026-06-04-paper-intensive-reading-design.md)
- [实施计划](docs/superpowers/plans/2026-06-04-paper-intensive-reading-PLAN.md)

## 许可

MIT
```

- [ ] **Step 4: 写 SECURITY.md**

`SECURITY.md`:
```markdown
# 安全说明

本 skill 实现了多层安全防护：

## NumPy 沙箱

用户提供的 NumPy 代码运行在子进程中，使用：
- AST 静态分析（白名单 imports + 黑名单 names）
- 资源限制（CPU 时间、内存）
- 输出截断（最大 10KB）

禁止的操作：
- 文件 I/O（`open`, `os`, `subprocess`）
- 网络访问（`requests`, `urllib`, `socket`）
- 代码自省（`__class__`, `__bases__`, `getattr`）
- 危险导入（`pickle`, `ctypes`, `cffi`）

详见 `tests/safety/test_safety.py`。

## PDF 解析安全

- 用 `pikepdf` 替代 `PyPDF2`（更安全的解析器）
- 拒绝带 JavaScript / 宏的 PDF
- 拒绝加密 PDF
- 用 `.paper-skill.json` 配置 vault 路径，避免路径注入

## arXiv 输入校验

arXiv ID 必须匹配 `^\d{4}\.\d{4,5}(v\d+)?$`。URL 必须包含 `arxiv.org`。
```

- [ ] **Step 5: 跑最终全量测试**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run pytest tests/unit tests/integration tests/safety -v 2>&1 | tail -30
```

- [ ] **Step 6: 跑 lint**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run ruff check paper-intensive-reading/ tests/
```

- [ ] **Step 7: 跑类型检查**

```bash
cd /Users/zhangjing/Documents/论文精度
uv run mypy paper-intensive-reading/
```

- [ ] **Step 8: 最终提交**

```bash
cd /Users/zhangjing/Documents/论文精度
git add README.md SECURITY.md
git commit -m "docs: complete README and SECURITY for v1.0 release"
git log --oneline | head -20
```

---

## 任务总览

到此所有 17 阶段、~50 个任务完成。

### 阶段汇总

| 阶段 | 任务数 | 状态 |
|------|--------|------|
| P1 项目骨架 | T1.1-T1.4 (4) | ✅ |
| P2 arxiv_fetch | T2.1-T2.5 (5) | ✅ |
| P3 pdf_parse | T3.1-T3.5 (5) | ✅ |
| P4 extract_figures | T4.1-T4.2 (2) | ✅ |
| P5 render_formula | T5.1-T5.2 (2) | ✅ |
| P6 numpy_runner | T6.1-T6.5 (5) | ✅ |
| P7 math_ladder + bilingual | T7.1-T7.3 (3) | ✅ |
| P8 formula_explainer | T8.1-T8.3 (3) | ✅ |
| P9 paper_store | T9.1-T9.3 (3) | ✅ |
| P10 to_markdown | T10.1-T10.3 (3) | ✅ |
| P11 to_obsidian | T11.1-T11.3 (3) | ✅ |
| P12 to_notion | T12.1-T12.3 (3) | ✅ |
| P13 image_gen | T13.1 (1) | ✅ |
| P14 survey | T14.1-T14.2 (2) | ✅ |
| P15 compare | T15.1-T15.2 (2) | ✅ |
| P16 SKILL.md | T16.1-T16.2 (2) | ✅ |
| P17 E2E + 性能 + 收尾 | T17.1-T17.3 (3) | ✅ |

**总任务数：~50 个**

### 验收清单

- [ ] 所有单元测试通过（行覆盖 ≥ 80%）
- [ ] 安全测试 100% 通过（沙箱不能被绕过）
- [ ] 集成测试（Attention 计算 + DB 持久化）通过
- [ ] 端到端测试（PDF → Paper → Markdown）通过
- [ ] 性能基准达标（端到端 < 3min）
- [ ] SKILL.md 完成（对话剧本 + 6 段公式 + 理解确认循环）
- [ ] README.md 和 SECURITY.md 完成

### 下一步

实施完成后，可选：
- 在真实 LLaMA 论文上跑一次（需要 arXiv 下载）
- 接到 opencode 的 skill 加载系统
- 发布 v1.0 tag

---

**实施计划完成。**
