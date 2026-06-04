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
