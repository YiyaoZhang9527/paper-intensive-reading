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
