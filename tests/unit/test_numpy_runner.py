import pytest
from paper_intensive_reading.numpy_runner import (
    validate_imports, validate_names, parse_code_safety
)
from paper_intensive_reading.errors import NumPyRunError


class TestValidateImports:
    def test_numpy_allowed(self):
        validate_imports("import numpy as np\nx = np.array([1,2,3])")

    def test_numpy_bare_allowed(self):
        validate_imports("import numpy\nx = numpy.array([1,2,3])")

    def test_os_blocked(self):
        with pytest.raises(NumPyRunError) as exc:
            validate_imports("import os")
        assert exc.value.subtype == "forbidden_import"

    def test_subprocess_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import subprocess")

    def test_requests_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import requests")

    def test_urllib_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("from urllib.request import urlopen")

    def test_sys_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_imports("import sys")


class TestValidateNames:
    def test_safe_names(self):
        validate_names("x = 1\ny = x + 2")

    def test_open_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("open('/etc/passwd')")

    def test_exec_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("exec('print(1)')")

    def test_eval_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("eval('1+1')")

    def test_getattr_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("getattr(np, 'array')")

    def test_globals_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("globals()['__builtins__']")

    def test_dunder_blocked(self):
        with pytest.raises(NumPyRunError):
            validate_names("x.__class__.__bases__")


class TestParseCodeSafety:
    def test_safe_code_passes(self):
        parse_code_safety("import numpy as np\nx = np.array([1,2,3])")

    def test_combined_violations(self):
        with pytest.raises(NumPyRunError):
            parse_code_safety("import os\nopen('/etc/passwd')")

    def test_syntax_error_caught(self):
        with pytest.raises(NumPyRunError) as exc:
            parse_code_safety("import numpy as np\nx = (1,2,3")
        assert exc.value.subtype == "syntax"


class TestRunCode:
    def test_simple_execution(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import numpy as np\nx = np.array([1, 2, 3])\nprint(x.sum())"
        result = run(code)
        assert result.ok
        assert "6" in result.stdout

    def test_timeout(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import numpy as np\nwhile True: np.zeros((1000, 1000))"
        result = run(code, timeout=2)
        assert not result.ok
        assert result.error_subtype == "timeout"

    def test_runtime_error(self):
        from paper_intensive_reading.numpy_runner import run
        code = "import numpy as np\nx = np.array([1, 2])\nprint(x[10])"
        result = run(code)
        assert not result.ok
        assert "IndexError" in result.stderr

    def test_syntax_error_caught(self):
        from paper_intensive_reading.numpy_runner import run
        code = "x = (1, 2,"
        result = run(code)
        assert not result.ok
        assert result.error_subtype == "syntax"

    def test_output_truncation(self):
        from paper_intensive_reading.numpy_runner import run
        code = "print('x' * 20000)"
        result = run(code, max_output=1024)
        assert result.ok
        assert len(result.stdout) <= 2048
