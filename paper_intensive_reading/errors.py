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
