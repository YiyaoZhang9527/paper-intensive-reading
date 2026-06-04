"""集成测试：跑完整的 Attention 三对照例子。"""
import pytest
from paper_intensive_reading.numpy_runner import run


@pytest.mark.integration
def test_attention_three_way_verification():
    code = """
import numpy as np
d_k = 4
Q = np.array([[1, 0, 1, 0],
              [0, 1, 0, 1],
              [1, 1, 0, 0]])
K = np.array([[1, 1, 0, 0],
              [0, 1, 1, 0],
              [1, 0, 0, 1]])
V = np.array([[0.5, 0.5],
              [0.8, 0.2],
              [0.3, 0.7]])
scores = Q @ K.T
print(f"Step 1 (QK^T) =\\n{scores}")
scores = scores / np.sqrt(d_k)
print(f"Step 2 (/sqrt({d_k})) =\\n{scores}")
def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)
weights = softmax(scores)
print(f"Step 3 (softmax) =\\n{weights}")
output = weights @ V
print(f"Step 4 (×V) =\\n{output}")
"""
    result = run(code, timeout=10)
    assert result.ok, f"代码运行失败: {result.error_message}"
    assert "Step 1" in result.stdout
    assert "Step 4" in result.stdout
