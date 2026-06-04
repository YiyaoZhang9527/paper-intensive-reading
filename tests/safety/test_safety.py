"""沙箱绕过测试：确保 numpy_runner 不能执行危险操作。"""
import pytest
from paper_intensive_reading.numpy_runner import run, parse_code_safety
from paper_intensive_reading.errors import NumPyRunError


class TestSandboxBypass:
    def test_os_system_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import os\nos.system('whoami')")

    def test_subprocess_run_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import subprocess\nsubprocess.run(['ls'])")

    def test_open_file_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("open('/etc/passwd').read()")

    def test_dunder_traversal_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("x = ().__class__.__bases__[0].__subclasses__()")

    def test_eval_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("eval('1+1')")

    def test_exec_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("exec('import os')")

    def test_getattr_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("getattr(__builtins__, 'open')")

    def test_socket_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import socket")

    def test_urllib_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("from urllib.request import urlopen")

    def test_pickle_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import pickle")

    def test_ctypes_blocked(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import ctypes")


class TestRealisticUse:
    def test_attention_calculation(self):
        code = """
import numpy as np
Q = np.array([[1, 0, 1, 0]])
K = np.array([[1, 1, 0, 0]])
V = np.array([[0.5, 0.5]])
scores = Q @ K.T / np.sqrt(4)
def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()
weights = softmax(scores)
output = weights @ V
print(f"scores: {scores}")
print(f"weights: {weights}")
print(f"output: {output}")
"""
        result = run(code)
        assert result.ok
        assert "scores:" in result.stdout
        assert "output:" in result.stdout

    def test_matrix_multiplication(self):
        code = """
import numpy as np
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
print(A @ B)
"""
        result = run(code)
        assert result.ok
        assert "19" in result.stdout
