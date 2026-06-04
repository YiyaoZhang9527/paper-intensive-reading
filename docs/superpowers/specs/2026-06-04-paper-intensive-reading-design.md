# 论文精读 Skill 设计文档

**日期**：2026-06-04
**作者**：zhangjing
**状态**：Draft（待用户审阅）
**目标版本**：v1.0

## 1. 概述

### 1.1 目标

为 AI/ML/CV/NLP 等计算机领域的研究者/学生提供一个**对话式**论文精读 skill。该 skill 像一位耐心的导师，带领用户从一篇 arXiv 论文出发：

- 自动下载/解析论文
- 逐节讲解，自适应调整深度
- 用**小学数学基础**讲解所有公式（带 NumPy 代码 + 实际运行 + 三对照验证）
- 强制做**理解确认循环**，拒绝"模糊不懂"
- 沉淀精读笔记到本地 Markdown / Obsidian / Notion 三端
- 支持单篇精读 / 多篇对比 / 阅读清单 / 领域调研四种模式

### 1.2 范围

**领域**：AI/ML/CV/NLP（含 LLM、Agent、推荐系统等）
**论文语言**：英文 / 中文（arXiv 为主，含会议论文、综述）
**用户数学基础**：预设小学水平（每公式必带概念阶梯讲解）
**输出语言**：始终中文 + 中英双语术语对照

### 1.3 不在范围内（v1）

- 论文写作 / 投稿辅助
- 代码完整复现实验（仅讲解 + 关键公式 NumPy 演示）
- 音视频附件处理
- 非计算机领域论文（结构化模板可能不适用）
- 商业数据库（如 Web of Science）的检索
- 论文推荐算法（仅基于引用 + 时效做粗排）

## 2. 架构总览

### 2.1 目录结构

```
paper-intensive-reading/
├── SKILL.md                    # 主入口：对话流程、模式、触发方式
├── scripts/
│   ├── arxiv_fetch.py         # 下载 arXiv PDF / 解析 BibTeX / 标题搜 arXiv
│   ├── pdf_parse.py           # PDF → 结构化 JSON
│   ├── extract_figures.py     # 从 PDF 抠图、保存为 PNG
│   ├── render_formula.py      # LaTeX → 公式图
│   ├── numpy_runner.py        # 安全执行 NumPy 代码
│   ├── formula_explainer.py   # 公式讲解 6 段模板（prompt 编排）
│   ├── math_ladder.py         # 概念阶梯导航
│   ├── bilingual.py           # 中英术语映射
│   ├── image_gen.py           # 图像生成 fallback 链
│   ├── paper_store.py         # 本地仓库（SQLite）
│   ├── survey.py              # 领域调研
│   ├── compare.py             # 多论文对比
│   ├── to_markdown.py         # 渲染精读笔记
│   ├── to_obsidian.py         # 推送到 Obsidian
│   ├── to_notion.py           # 推送到 Notion
│   ├── types.py               # Paper/Section/Formula 等数据模型
│   └── errors.py              # 错误类型与中文错误消息
├── references/
│   ├── math-ladder.md         # 数学概念阶梯（0-7 层）
│   ├── paper-templates.md     # 4 种模式笔记模板
│   ├── ai-ml-concepts.md      # 零基础 AI/ML 概念库
│   ├── image-providers.md     # 图像生成 fallback 链配置
│   └── formula-glossary.md    # 常见公式符号对照
├── data/
│   ├── reading-list.sqlite
│   ├── papers/
│   │   ├── pdfs/<arxiv-id>.pdf
│   │   ├── notes/<arxiv-id>-精读笔记.md
│   │   ├── figures/<arxiv-id>/
│   │   ├── formulas/<arxiv-id>/
│   │   ├── drafts/<arxiv-id>-in-progress.md
│   │   └── logs/
│   └── cache/
│       ├── arxiv-search/<query>.json
│       └── parsed/<arxiv-id>.json
└── tests/
    ├── unit/
    ├── integration/
    ├── e2e/
    ├── performance/
    ├── snapshots/
    └── fixtures/
```

### 2.2 核心理念

- **SKILL.md** 是"对话剧本"——告诉 AI 怎么跟用户聊、什么时候调用哪个脚本
- **scripts/** 是"工程化"——所有 I/O、解析、渲染都封装在 Python 里
- **references/** 是"上下文补给"——给 AI 提供领域知识（公式表、概念解释模板）
- **data/** 是"用户资产"——所有 PDF、笔记、阅读清单都落盘

### 2.3 触发方式

- `/paper-read <id>` — 单篇精读
- `/paper-read --compare <id1> <id2>` — 多篇对比
- `/paper-list` — 查看阅读清单
- `/paper-list --add <id>` — 添加到清单
- `/paper-survey "<query>"` — 领域调研
- `/paper-errors` — 查看错误日志

## 3. 核心数据模型

```python
# scripts/types.py
@dataclass
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    affiliations: list[str]
    abstract: str
    published: date
    pdf_path: str
    sections: list[Section]
    figures: list[Figure]
    tables: list[Table]
    algorithms: list[Algorithm]
    references: list[Reference]

@dataclass
class Section:
    number: str
    title: str
    level: int
    paragraphs: list[Paragraph]
    formulas: list[Formula]

@dataclass
class Formula:
    number: str
    latex: str
    context_before: str
    context_after: str
    symbols: dict[str, str]

@dataclass
class Figure:
    number: str
    caption: str
    image_path: str
    page: int

@dataclass
class Table:
    number: str
    caption: str
    headers: list[str]
    rows: list[list[str]]

@dataclass
class Algorithm:
    number: str
    title: str
    pseudocode: str
    language_hint: str
```

## 4. 脚本清单与职责

| # | 脚本 | 职责 | 关键接口 |
|---|------|------|----------|
| 1 | `arxiv_fetch.py` | 多源获取 PDF | `fetch(source) -> pdf_path` |
| 2 | `pdf_parse.py` | PDF → 结构化 JSON | `parse(pdf_path) -> Paper` |
| 3 | `extract_figures.py` | 抠图 / 矢量页渲染 | `extract(pdf, out_dir) -> manifest` |
| 4 | `render_formula.py` | LaTeX → 图片 | `render(latex, out) -> png_path` |
| 5 | `numpy_runner.py` | 安全运行 NumPy 代码 | `run(code) -> {stdout, ok}` |
| 6 | `formula_explainer.py` | 生成 6 段公式讲解 | `explain(formula, ctx) -> segments` |
| 7 | `math_ladder.py` | 概念阶梯导航 | `path_for(topic) -> layers[]` |
| 8 | `bilingual.py` | 中英术语映射 | `translate(en) -> {zh, gloss}` |
| 9 | `image_gen.py` | 图像生成 fallback 链 | `generate(prompt) -> img_path` |
| 10 | `paper_store.py` | 阅读清单/进度 (SQLite) | CRUD on `papers` table |
| 11 | `survey.py` | 领域调研，拉 arXiv 列表 | `search(query) -> Paper[]` |
| 12 | `compare.py` | 多论文并排对比 | `compare(ids, aspects) -> table` |
| 13 | `to_markdown.py` | 渲染最终笔记 | `render(paper, ctx) -> md_path` |
| 14 | `to_obsidian.py` | 落盘到 Obsidian | `save(md, pdf, vault)` |
| 15 | `to_notion.py` | 推送到 Notion | `push(md, pdf, db_id)` |

## 5. 主调用流程

```
User: /paper-read 2302.13971
  ↓
arxiv_fetch.py: 下载 PDF 到 data/papers/pdfs/
  ↓
pdf_parse.py: parse → Paper 对象（含 sections/formulas/figures）
  ↓ (同时触发)
extract_figures.py: 抠图到 data/papers/figures/<id>/
  ↓
paper_store.py: add_paper() + update_status("在读")
  ↓
SKILL 主循环:
  对每个 Section:
    对每个 Formula:
      math_ladder.py: 决定从哪层概念讲起
      formula_explainer.py: 生成 6 段讲解
        - 段[5] 调 numpy_runner（带实际运行）
        - 段[6] 调 render_formula（生成公式图）
        - 段[3] 调 bilingual（中英术语）
      6 段输出 + 理解确认循环
      user_state 写回 paper_store
  ↓
to_markdown.py: render() → 精读笔记 .md
  ↓
to_obsidian.py + to_notion.py: 多端同步（PDF + MD）
  ↓
paper_store.py: update_status("已读完")
```

## 6. 4 种模式

| 模式 | 入口 | 走的脚本路径 |
|------|------|------------|
| `read`（单篇） | `/paper-read <id>` | arxiv_fetch → parse → 主循环 → markdown → 多端 |
| `compare`（对比） | `/paper-read --compare <id1> <id2>` | arxiv_fetch × N → parse × N → compare.py → markdown（多栏）→ 多端 |
| `list`（清单） | `/paper-list` / `/paper-list --add` | 直接 paper_store.py 读写；可选 arxiv_fetch 补 PDF |
| `survey`（调研） | `/paper-survey "<query>"` | survey.py → arxiv 搜索 → paper_store 批量添加 → 可选进入 read |

## 7. 对话流程

### 7.1 标准化开场

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

### 7.2 章节引导模式的核心循环

每节 4 步：

1. **推送本节内容**：1-2 段白话总结 + 3-5 个要点（带中英对照）+ 关键公式（LaTeX + 符号 + 直觉）+ 算法伪代码 + 图表描述
2. **自适应难度检查**："这节的深度合适吗？太深/太浅/刚好？"
3. **进度 + 决定**："我们已完成 Abstract + Intro (2/6)。继续下一节？/ 重讲这段？/ 跳到 Result？"
4. **用户随时插入**：追问、举例、跳节、保存

### 7.3 关键点专讲模式

```
Skill: 通读后我标出 5 个最关键的点：
       1. RMSNorm 替代 LayerNorm 的动机和效果
       2. SwiGLU 激活函数
       3. RoPE 旋转位置编码
       4. 训练数据混合策略
       5. 评估方法
       选一个先开始？或全讲？
```

### 7.4 阅读清单 / 调研模式

- **List 模式**：展示待读/在读/已读完清单
- **Survey 模式**：从 arXiv 拉取近 6 个月 Top 10 论文

### 7.5 硬约束（对话节奏）

- 每节讲解不超过 800 字
- 每个公式都跟一段白话
- 每完成一节必问一次反馈
- 每 3 节提醒一次保存
- 用户问"X 在哪"时直接定位章节

## 8. 公式讲解 6 段结构

每讲一个公式必须输出以下 6 段：

### [1] 原始形式（LaTeX）
```latex
\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
```

### [2] 白话翻译
"每个词，去看看其他词跟自己的相关度，然后按相关度加权汇总信息。"

### [3] 逐符号解释（带阶梯层号）
- $Q$（Query，查询向量，第 5 层）
- $K$（Key，键向量，第 5 层）
- ...

### [4] 直觉类比（生活场景）
"想象你在图书馆查资料。Q 是你的'问题'，K 是每本书的'索引卡'..."

### [5] 详细计算示例
- 用 d_k=4 的极小例子
- 逐步手算可验证
- 用真实场景词（"我/爱/你"）

### [6] NumPy 代码实现 + 实际运行结果
- 只用 NumPy
- 每步有 print
- **三对照表**：手算 = 代码 = 跑出

### 8.1 公式讲解的硬约束

- 6 段都不能省
- 符号解释必须带阶梯层号
- 直觉类比必须用生活场景（不用 AI 圈黑话）
- NumPy 代码必须**实际运行**（不是只贴出来）
- 三对照表是必输出

## 9. 理解确认循环

每讲完一个公式，强制执行：

```
Skill: ✅ 这个公式讲完了。

       请用你自己的话回答下面 3 个问题中的**任意 1 个**：
       1) 这个公式在算什么？（用一句话，不许抄我的）
       2) 例子里的第 X 步，对应公式的哪个符号？
       3) 如果 $d_k$ 从 4 改成 16，第 2 步会发生什么变化？

       如果你回答"我懂了但说不出来" — 我不接受这个答案。
       如果你回答"我不懂" — 请具体说不懂哪一步、哪个符号、哪个比喻。
```

### 9.1 拒绝/通过的判定规则

| 用户回答 | skill 反应 |
|---------|-----------|
| 答对至少 1 题 | ✅ 通过，进入下一节 |
| 答错/答偏 | 🔁 指出错在哪一环节，重讲 |
| "我不懂"（没说哪里不懂） | ❌ 拒绝，要求具体指出 |
| "我懂了但说不出来" | ❌ 拒绝，要求至少 5 字描述 |
| "跳吧" | ⚠️ 警告一次，再坚持才跳（打 skipped 标记） |
| 用户问反问 | ✅ 好信号，回到对应阶梯层重讲 |

### 9.2 教学纪律扩展

- **每个章节讲完**走简化版理解确认
- **每个算法伪代码、图表描述**后也要走确认
- 唯一跳过确认的场景：用户明确说 skip（记录 skipped）

### 9.3 失败自适应

同一类问题失败 3 次自动切换策略：
- 用图像代替文字（调用 image_gen 链）
- 用代码运行代替推导（让用户跑 Python 看输出）
- 用类比升级（换一个更贴近的生活场景）

## 10. 数学概念阶梯

`references/math-ladder.md` 预置 8 层概念：

- **第 0 层**：算术（加减乘除、分数、小数、百分数）
- **第 1 层**：基本代数（用字母代替数字、未知数）
- **第 2 层**：函数与图像
- **第 3 层**：指数和对数
- **第 4 层**：概率与统计
- **第 5 层**：向量与矩阵（LLM 必备）
- **第 6 层**：导数与梯度
- **第 7 层**：注意力机制的数学（Q/K/V、Softmax、Attention）

skill 遇到公式时自动查询阶梯，决定讲解起点。

### 10.1 自适应联动

- 用户反馈"太深" → 降低讲解起点
- 同一概念失败 3 次 → 切换图像 / 代码 / 类比策略

## 11. 图像生成 Fallback 链

```
references/image-providers.md:

1. nano-banana-pro (Gemini 3 Pro Image, 默认)
2. MiniMax-M3 (当前模型，能生成 SVG / Mermaid / matplotlib)
3. GLM (zhipu, 备选)

skill 在需要示意图时按顺序试，全失败用纯 ASCII 兜底
```

## 12. 落盘目录与命名规范

```
data/
├── reading-list.sqlite
├── papers/
│   ├── pdfs/<arxiv-id>.pdf              # 权威 PDF 副本
│   ├── notes/<arxiv-id>-精读笔记.md      # 最终笔记
│   ├── figures/<arxiv-id>/fig-N.png
│   ├── formulas/<arxiv-id>/eq-N.png
│   ├── drafts/<arxiv-id>-in-progress.md
│   └── logs/<arxiv-id>-conversation.jsonl
└── cache/
    ├── arxiv-search/<query>.json
    └── parsed/<arxiv-id>.json
```

| 资源 | 命名规则 |
|------|---------|
| arxiv ID 文件 | 去掉版本号的裸 ID：`2302.13971.pdf` |
| 笔记 | `<id>-精读笔记.md` |
| 图表 | `fig-<n>.png` |
| 公式图 | `eq-<n>.png` |
| 算法图 | `alg-<n>.png` |
| 草稿 | `<id>-in-progress.md` |

## 13. 笔记 Markdown 模板

```markdown
---
arxiv_id: 2302.13971
title: "LLaMA: ..."
authors: [...]
year: 2023
status: 已读完
tags: [llm, foundation-model, pretraining]
depth_pref: elementary
---

# <论文标题>

> **TL;DR**：[一句话]

## 1. 背景与动机
## 2. 核心贡献
## 3. 方法详解（含公式 6 段讲解）
## 4. 实验与结果
## 5. 讨论与启示
## 6. 术语表（中英对照）
## 7. 参考资料
## 8. 理解自检记录
```

### 13.1 对比模式笔记结构

`/paper-read --compare <id1> <id2> [<id3>...]` 生成的笔记：

```markdown
# 对比：A (LLaMA) vs B (GPT-3)

## 概览对比
| 维度 | A: LLaMA | B: GPT-3 |
|------|---------|----------|
| 时间 | 2023.02 | 2020.05 |
| 参数量 | 7B-65B | 175B |
| 训练数据 | 公开 | 未公开 |

## 关键方法对比
### 归一化
- LLaMA: **RMSNorm**（详细讲解见 A 笔记 §3.2）
- GPT-3: **LayerNorm**（详细讲解见 B 笔记 §3.1）

### 位置编码
- LLaMA: **RoPE**
- GPT-3: **Learned Absolute Position**

## 实验对比
[并排的表格 + 图表]

## 借鉴决策
- 想做小模型：选 LLaMA 路径
- 想做大模型：参考 GPT-3，但 LLaMA 的训练 trick 也可借鉴
```

### 13.2 调研模式笔记结构

`/paper-survey "<query>"` 生成 `data/papers/surveys/<query>-<date>.md`：

```markdown
# 调研：LLM Agents (截至 2026-06)

> 来自 arXiv 搜索，Top 10 论文按引用 + 时效排序

## 1. Toolformer (Schick et al., 2023)
**为什么读**：开山工作
**核心方法**：自监督构造工具调用数据
**arXiv**: [2302.04761](https://arxiv.org/abs/2302.04761)
**状态**：已添加到阅读清单 ✓

## 2. ReAct (Yao et al., 2022)
...

## 阅读路径建议
按这个顺序读，基础→进阶：
1. ReAct (基础范式)
2. Toolformer (工具调用)
3. ...

## 添加到清单
[ ] 全部添加 / 输入编号选择性添加
```

## 14. 多端同步

| 端 | 同步什么 | 何时同步 | 实现 |
|----|---------|---------|------|
| 本地 MD | 笔记 + PDF | 实时 | 写到 `data/papers/notes/` |
| Obsidian | MD + PDF | 笔记完成时 | `to_obsidian.py` |
| Notion | MD + PDF | 笔记完成时 | `to_notion.py` |

**Obsidian 布局**：
```
~/Documents/ObsidianVault/Papers/
├── 2302.13971-LLaMA/
│   ├── 2302.13971-精读笔记.md
│   ├── 2302.13971.pdf
│   └── figures/
└── _index.md
```

**幂等规则**：本地 MD 是权威源；推送时检查目标是否存在，已存在则询问（覆盖/跳过/重命名）。

## 15. 错误处理

### 15.1 错误层次

| 层级 | 触发场景 | 恢复策略 |
|------|---------|---------|
| L1 | 用户输入 | 立刻反馈，让用户改 |
| L2 | 网络 | 重试 3 次（指数退避） |
| L3 | 资源（PDF 损坏） | 降级或中止 |
| L4 | 执行（NumPy 失败） | 简化例子重试 |
| L5 | 保存（Obsidian/Notion） | 重试 → 失败保留本地 + 警告 |
| L6 | LLM | 换 prompt / 换模型重试 |

### 15.2 错误消息模板

所有错误用中文友好消息（`scripts/errors.py`），禁止抛原始 Python 异常。

### 15.3 降级策略

| 失败点 | 降级方案 |
|-------|---------|
| 公式图片生成失败 | 保留 LaTeX + ASCII 艺术 |
| 公式代码运行失败 | 保留手算例子，省略第 6 段 |
| 图表提取失败 | 保留 PDF 链接 + 文字描述 |
| Obsidian 失败 | 仅本地保存 + 警告 |
| Notion 失败 | 本地 + Obsidian + 警告 |
| LLM 限流 | 排队 30 秒 |

### 15.4 状态恢复

- **对话中断**：检测 drafts，提示续读
- **数据库与文件不一致**：启动时 reconcile，报告
- **多端同步冲突**：哈希对比，询问用户

## 16. 安全边界

### 16.1 NumPy 沙箱

```python
ALLOWED_IMPORTS = {"numpy", "numpy as np"}
FORBIDDEN_NAMES = {"os", "sys", "subprocess", "shutil", "open", 
                    "exec", "eval", "socket", "urllib", ...}
MAX_EXECUTION_TIME = 10  # 秒
MAX_MEMORY_MB = 256
MAX_OUTPUT_BYTES = 10240
```

### 16.2 PDF 解析沙箱

- 用 pikepdf（非 PyPDF2，对恶意 PDF 更安全）
- 拒绝带 JavaScript / 宏的 PDF
- 拒绝加密 PDF
- 拒绝扫描件（无文字层）

### 16.3 arXiv 输入校验

```python
ARXIV_ID_PATTERN = re.compile(r"^\d{4}\.\d{4,5}(v\d+)?$")
```

## 17. 测试策略

### 17.1 测试金字塔

- **单元测试**（30-50 个）：每个脚本独立，pytest，行覆盖 ≥ 80%
- **集成测试**（5-8 个）：脚本间组合
- **端到端测试**（1-2 个）：完整跑一篇论文，慢
- **性能基准**：端到端 < 3 分钟
- **安全测试**：所有 NumPy 沙箱入口 100% 覆盖
- **LLM 输出质量**：手动验证清单

### 17.2 关键测试点

- `test_arxiv_fetch.py`：4 种输入源
- `test_pdf_parse.py`：元数据、章节、公式、图表
- `test_numpy_runner.py`：安全关键（拒绝 os/sys/subprocess、超时）
- `test_render_formula.py`：LaTeX 渲染
- `test_paper_store.py`：CRUD
- `test_bilingual.py`：术语翻译
- `test_math_ladder.py`：前置概念

### 17.3 E2E 测试

```python
def test_full_llama_intensive_read():
    """完整跑 LLaMA 论文 → 验证 SQLite/笔记/图表/多端都有产物"""
```

### 17.4 LLM 输出手动验证清单

公式讲解按 6 段 + 理解确认循环逐项 ✓。

## 18. 性能目标

| 操作 | 目标时间 |
|------|---------|
| 解析单篇 PDF | < 10s |
| 抠图 | < 30s |
| 公式渲染（单个） | < 1s |
| 公式讲解生成（含 NumPy 运行） | < 30s |
| 端到端单篇精读 | < 3min |
| 调研模式拉 Top 10 论文 | < 60s |

## 19. 边界场景清单

### 输入边界
- arXiv ID 格式错 → 提示正确格式
- PDF 不存在 → 提示检查路径
- 标题搜不到 → 提示换关键词
- PDF 加密 → 拒绝，让用户提供解密版
- 扫描件 PDF → 提示不支持 OCR
- PDF > 50 页 → 提示用户确认

### 对话边界
- 用户跑题 → 温和拉回
- 用户要求"重讲" → 回到该节重置状态
- 用户要求"跳过" → 警告一次，再坚持则打 skipped
- 上下文超长（> 100K tokens）→ 自动总结前文

### 内容边界
- 论文无公式 → 跳过公式讲解
- 论文无图表 → 跳过图表
- 公式图片生成失败 → 降级到 ASCII
- 综述论文 → 自动用 survey 模板

### 系统边界
- 磁盘空间不足 → 写入前检查
- SQLite 锁 → 重试 3 次
- LLM API 限流 → 排队重试
- 备用模型切换失败 → 提示用户重试

## 20. 实施里程碑

| 阶段 | 内容 | 验收 |
|------|------|------|
| M1 | 骨架（SKILL.md + types.py + paper_store.py + SQLite schema） | 单元测试通过 |
| M2 | arxiv_fetch + pdf_parse + extract_figures | 能下载并解析 LLaMA |
| M3 | render_formula + numpy_runner（沙箱） | 公式图生成、代码安全运行 |
| M4 | formula_explainer + math_ladder + bilingual | 6 段讲解模板 + 概念阶梯 |
| M5 | to_markdown + 4 种模式模板 | 完整笔记生成 |
| M6 | to_obsidian + to_notion | 多端同步 |
| M7 | survey + compare + list 模式 | 4 种模式齐全 |
| M8 | 错误处理 + 降级 + 安全 | 错误消息、降级策略、沙箱 |
| M9 | 完整测试套件 + E2E | 端到端 < 3min，所有测试通过 |
| M10 | 文档 + 优化 | 性能达到目标 |

## 21. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| PDF 解析准确率低 | 公式/章节识别错 | 多个 PDF 库对比（PyMuPDF + pdfplumber + pikepdf） |
| NumPy 沙箱被绕过 | 安全漏洞 | 多重检查：AST 静态分析 + 运行时限制 + 输出过滤 |
| LLM 输出不稳定 | 公式讲解质量波动 | prompt 模板严格 + 6 段硬约束 + 手动验证清单 |
| 公式图片渲染失败 | 用户体验差 | 多 fallback：matplotlib mathtext → KaTeX → ASCII |
| LLM 上下文爆 | 长论文无法处理 | 分段处理 + 自动总结前文 + 草稿文件 |
| Obsidian/Notion API 变更 | 同步失败 | 适配层抽象，配置与代码分离 |

## 22. 开放问题（v1 不解决）

- 多用户协作（共享阅读清单）
- 论文版本对比（v1 vs v2 的 diff）
- 自动生成阅读笔记的二次摘要（一句话总结 → 推文）
- 集成 Zotero（导入已有 library）
- 论文引用图谱（visualize）
- 跨语言翻译（中文论文自动翻译到英文笔记）
- 与 code reproduction skill 联动（读论文 → 复现实验）
