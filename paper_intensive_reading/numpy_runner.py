"""安全执行用户提供的 NumPy 代码。"""
import ast
from .errors import NumPyRunError

ALLOWED_IMPORTS = {"numpy", "numpy as np"}
FORBIDDEN_NAMES = {
    "os", "sys", "subprocess", "shutil", "pathlib", "glob",
    "open", "exec", "eval", "compile", "input",
    "socket", "urllib", "requests", "http", "ftplib", "smtplib",
    "ctypes", "cffi", "multiprocessing", "threading",
    "__import__", "getattr", "globals", "locals", "vars", "dir",
    "breakpoint", "memoryview",
}
FORBIDDEN_ATTRS = {
    "__class__", "__bases__", "__subclasses__", "__globals__",
    "__code__", "__dict__", "__module__", "__import__",
}


def validate_imports(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod != "numpy":
                    raise NumPyRunError("forbidden_import", detail=f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod != "numpy":
                raise NumPyRunError("forbidden_import", detail=f"from {node.module} import ...")


def validate_names(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise NumPyRunError("forbidden_name", detail=f"name '{node.id}'")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            raise NumPyRunError("forbidden_name", detail=f"attribute '{node.attr}'")


def parse_code_safety(code: str) -> ast.Module:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise NumPyRunError("syntax", detail=str(e)) from e
    validate_imports(code)
    validate_names(code)
    return tree


import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from dataclasses import dataclass  # noqa: E402


@dataclass
class RunResult:
    ok: bool
    stdout: str
    stderr: str
    duration_s: float
    error_subtype: str = ""
    error_message: str = ""

    def to_dict(self) -> dict:
        return {
            "ok": self.ok, "stdout": self.stdout, "stderr": self.stderr,
            "duration_s": self.duration_s, "error_subtype": self.error_subtype,
            "error_message": self.error_message,
        }


_RUNNER_TEMPLATE = """
import sys
import resource
try:
    resource.setrlimit(resource.RLIMIT_AS, (__MEMORY_MB__ * 1024 * 1024, __MEMORY_MB__ * 1024 * 1024))
except (ValueError, OSError):
    pass
import numpy as np
try:
__CODE__
except Exception as e:
    print(f"__ERROR__{type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
"""


def run(
    code: str, timeout: int = 10, memory_mb: int = 256, max_output: int = 10240,
) -> RunResult:
    """在子进程中安全执行 NumPy 代码。"""
    try:
        parse_code_safety(code)
    except NumPyRunError as e:
        return RunResult(ok=False, stdout="", stderr="", duration_s=0.0,
                         error_subtype=e.subtype, error_message=str(e.context.get("detail", "")))

    indented = "\n".join("    " + line for line in code.split("\n"))
    runner_src = (
        _RUNNER_TEMPLATE
        .replace("__CODE__", indented)
        .replace("__MEMORY_MB__", str(memory_mb))
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(runner_src)
        tmp_path = f.name

    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, tmp_path], capture_output=True, text=True,
            timeout=timeout, env={"PATH": "/usr/bin:/bin", "PYTHONPATH": ""},
        )
        duration = time.time() - start
        stdout = proc.stdout[:max_output]
        stderr = proc.stderr[:max_output]

        if proc.returncode == 0:
            return RunResult(ok=True, stdout=stdout, stderr=stderr, duration_s=duration)

        if "SyntaxError" in stderr:
            subtype = "syntax"
        elif "MemoryError" in stderr:
            subtype = "memory"
        else:
            subtype = "runtime"
        return RunResult(ok=False, stdout=stdout, stderr=stderr, duration_s=duration,
                         error_subtype=subtype, error_message=stderr[:500])
    except subprocess.TimeoutExpired:
        duration = time.time() - start
        return RunResult(ok=False, stdout="", stderr="", duration_s=duration,
                         error_subtype="timeout", error_message=f"超过 {timeout} 秒")
    finally:
        try:
            from pathlib import Path
            Path(tmp_path).unlink()
        except Exception:
            pass
