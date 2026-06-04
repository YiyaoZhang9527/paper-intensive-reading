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
        sections_md += f"## {sec.number}. {sec.title}\n\n"
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
