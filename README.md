# Paper Intensive Reading Skill

对话式 AI/ML 论文精读 skill。

## 功能

- 从 arXiv 自动下载 PDF（支持 arXiv ID / URL / 标题 / BibTeX / 本地路径）
- 用**小学数学基础**讲解每个公式（带 NumPy 实际运行 + 三对照验证）
- 强制做**理解确认循环**，拒绝"模糊不懂"
- 沉淀笔记到本地 Markdown / Obsidian / Notion 三端
- 4 种模式：单篇精读 / 多篇对比 / 阅读清单 / 领域调研

## 安装

```bash
uv sync
```

## 使用

详见 [SKILL.md](SKILL.md) 里的触发方式和对话流程。

## 项目结构

```
paper_intensive_reading/   # Python 包
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
```

## 测试

```bash
# 全部测试
uv run pytest tests/

# 单元测试
uv run pytest tests/unit

# 性能测试
uv run pytest tests/performance

# 安全测试（沙箱）
uv run pytest tests/safety

# 覆盖率
uv run pytest --cov=paper_intensive_reading --cov-report=html
```

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
