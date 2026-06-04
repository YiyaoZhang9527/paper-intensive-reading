"""数学概念阶梯：决定讲公式时从哪层开始。"""

_CONCEPT_TO_LAYER: dict[str, int] = {
    "+": 0, "-": 0, "*": 0, "/": 0, "sum": 0, "average": 0, "min": 0, "max": 0,
    "x + y": 1, "x = 1": 1, "variable": 1, "unknown": 1,
    "f(x)": 2, "function": 2, "graph": 2,
    "exp": 3, "log": 3, "logarithm": 3, "exponential": 3, "power": 3,
    "probability": 4, "softmax": 4, "mean": 4, "variance": 4, "distribution": 4,
    "cross-entropy": 4,
    "vector": 5, "matrix": 5, "matrix multiply": 5, "matmul": 5,
    "dot product": 5, "QK": 5, "QK^T": 5, "Q·K": 5,
    "embedding": 5, "linear layer": 5,
    "rmsnorm": 5, "layernorm": 5, "batchnorm": 5, "normalization": 5,
    "gelu": 5, "relu": 5, "sigmoid": 5, "tanh": 5,
    "swiglu": 5,
    "derivative": 6, "gradient": 6, "chain rule": 6, "backpropagation": 6,
    "attention": 7, "self-attention": 7, "cross-attention": 7,
    "rope": 7, "qkv": 7, "Q": 7, "K": 7, "V": 7,
    "multi-head": 7, "transformer": 7,
}

LAYER_DESCRIPTIONS: dict[int, str] = {
    0: "第 0 层：算术（加减乘除、分数、小数、百分数）",
    1: "第 1 层：基本代数（用字母代替数字、未知数）",
    2: "第 2 层：函数与图像（输入输出、坐标）",
    3: "第 3 层：指数和对数（翻倍、对应的反向）",
    4: "第 4 层：概率与统计（可能性、平均数、方差）",
    5: "第 5 层：向量与矩阵（一列数、表格、乘法）",
    6: "第 6 层：导数与梯度（变化速度、最陡方向）",
    7: "第 7 层：注意力机制（Q/K/V、查字典）",
}

ALL_LAYERS = list(range(8))


def layers_for_concept(concept: str) -> list[int]:
    concept = concept.strip().lower()
    layer = _CONCEPT_TO_LAYER.get(concept)
    if layer is None:
        return [0]
    return [layer]


def path_for(topic: str) -> list[int]:
    layers = layers_for_concept(topic)
    max_layer = max(layers)
    return list(range(max_layer + 1))


def describe_layer(layer: int) -> str:
    if layer not in LAYER_DESCRIPTIONS:
        raise ValueError(f"层 {layer} 不存在（0-7）")
    return LAYER_DESCRIPTIONS[layer]
