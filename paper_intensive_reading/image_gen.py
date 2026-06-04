"""图像生成 fallback 链：nano-banana-pro → GLM → ASCII。"""
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
    """按 fallback 链生成图。最终兜底是 ASCII。

    注：PROVIDERS 由 setup_providers() 初始化；调用方可在外部 set PROVIDERS
    来注入自定义 provider（便于测试）。generate() 不会自动 reset PROVIDERS。
    """
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
