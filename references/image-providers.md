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

```bash
export NANO_BANANA_PRO_API_KEY="..."
export GLM_API_KEY="..."
```

skill 会自动检测哪些 provider 可用。
