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
