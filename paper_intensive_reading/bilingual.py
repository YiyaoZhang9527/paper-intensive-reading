"""中英术语映射。"""

KNOWN_TERMS: dict[str, dict[str, str]] = {
    "transformer": {"zh": "Transformer", "description": "基于自注意力的神经网络架构"},
    "attention": {"zh": "注意力", "description": "让模型关注输入中相关部分"},
    "self-attention": {"zh": "自注意力", "description": "同一序列内部各位置之间的注意力"},
    "cross-attention": {"zh": "交叉注意力", "description": "两个不同序列之间的注意力"},
    "multi-head attention": {"zh": "多头注意力", "description": "并行多组注意力"},
    "encoder": {"zh": "编码器", "description": "将输入映射为表示的模块"},
    "decoder": {"zh": "解码器", "description": "从表示生成输出的模块"},
    "embedding": {"zh": "嵌入", "description": "把离散符号映射为连续向量"},
    "token": {"zh": "词元", "description": "文本的最小处理单位"},
    "tokenization": {"zh": "分词", "description": "把文本切分为词元"},
    "vocabulary": {"zh": "词表", "description": "模型能识别的所有词元集合"},
    "fine-tuning": {"zh": "微调", "description": "在预训练模型上用特定数据继续训练"},
    "pre-training": {"zh": "预训练", "description": "在大规模数据上训练通用模型"},
    "transfer learning": {"zh": "迁移学习", "description": "把已学知识迁移到新任务"},
    "supervised learning": {"zh": "监督学习", "description": "用标注数据训练"},
    "unsupervised learning": {"zh": "无监督学习", "description": "用未标注数据训练"},
    "self-supervised": {"zh": "自监督", "description": "用数据自身作为监督信号"},
    "reinforcement learning": {"zh": "强化学习", "description": "通过奖励信号学习策略"},
    "rlhf": {"zh": "基于人类反馈的强化学习", "description": "RLHF"},
    "reward model": {"zh": "奖励模型", "description": "预测人类偏好的模型"},
    "gradient descent": {"zh": "梯度下降", "description": "沿梯度反方向更新参数"},
    "adam": {"zh": "Adam 优化器", "description": "自适应学习率优化算法"},
    "learning rate": {"zh": "学习率", "description": "参数更新的步长"},
    "batch size": {"zh": "批量大小", "description": "每次迭代用的样本数"},
    "epoch": {"zh": "轮次", "description": "完整过一遍训练集"},
    "backpropagation": {"zh": "反向传播", "description": "从损失反向计算梯度"},
    "layer normalization": {"zh": "层归一化", "description": "LayerNorm，按特征归一化"},
    "layernorm": {"zh": "层归一化", "description": "LayerNorm"},
    "rmsnorm": {"zh": "均方根归一化", "description": "用均方根做归一化，比 LayerNorm 更快"},
    "batch normalization": {"zh": "批归一化", "description": "按批量维度归一化"},
    "batchnorm": {"zh": "批归一化", "description": "BatchNorm"},
    "gelu": {"zh": "GELU 激活", "description": "高斯误差线性单元"},
    "relu": {"zh": "ReLU 激活", "description": "修正线性单元"},
    "sigmoid": {"zh": "Sigmoid", "description": "S 形激活，输出 0-1"},
    "softmax": {"zh": "Softmax", "description": "把向量变成概率分布"},
    "swiglu": {"zh": "SwiGLU", "description": "GLU 变体，用 Swish 激活"},
    "silu": {"zh": "SiLU/Swish", "description": "Sigmoid Linear Unit"},
    "positional encoding": {"zh": "位置编码", "description": "让模型感知序列位置"},
    "rope": {"zh": "旋转位置编码", "description": "RoPE，用旋转矩阵编码相对位置"},
    "llm": {"zh": "大语言模型", "description": "Large Language Model"},
    "foundation model": {"zh": "基础模型", "description": "大规模预训练通用模型"},
    "prompt": {"zh": "提示", "description": "输入给模型的指令或问题"},
    "in-context learning": {"zh": "上下文学习", "description": "在 prompt 里给示例让模型学习"},
    "few-shot": {"zh": "少样本", "description": "在 prompt 里给几个示例"},
    "zero-shot": {"zh": "零样本", "description": "不给示例直接让模型做"},
    "chain-of-thought": {"zh": "思维链", "description": "CoT，让模型逐步推理"},
    "hallucination": {"zh": "幻觉", "description": "模型生成不真实的内容"},
    "agent": {"zh": "智能体", "description": "能自主决策和行动的 AI 系统"},
    "tool use": {"zh": "工具使用", "description": "让 LLM 调用外部工具"},
    "function calling": {"zh": "函数调用", "description": "让 LLM 调用预定义函数"},
    "rag": {"zh": "检索增强生成", "description": "RAG，先检索相关文档再生成"},
    "retrieval": {"zh": "检索", "description": "从知识库找相关信息"},
    "vector database": {"zh": "向量数据库", "description": "存储和检索向量的数据库"},
    "benchmark": {"zh": "基准测试", "description": "标准化的评估任务"},
    "evaluation": {"zh": "评估", "description": "衡量模型性能"},
    "perplexity": {"zh": "困惑度", "description": "PPL，预测质量的逆指标"},
}


def translate(term: str) -> dict[str, str]:
    key = term.strip().lower()
    entry = KNOWN_TERMS.get(key)
    if entry:
        return {"en": term, "zh": entry["zh"], "description": entry.get("description", "")}
    return {"en": term, "zh": term, "description": ""}


def build_glossary(terms: list[str], with_description: bool = True) -> dict[str, dict[str, str]]:
    glossary: dict[str, dict[str, str]] = {}
    for term in terms:
        key = term.strip().lower()
        if key in glossary:
            continue
        entry = translate(term)
        glossary[key] = entry if with_description else {"zh": entry["zh"]}
    return glossary
