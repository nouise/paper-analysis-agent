"""
知识库名称生成器

支持多种命名风格：
- 学术风: "深度学习研究_0311"
- 随机风: "智能文档库_a3f9"
- 时间戳: "KB_20250311_143052"
"""

import random
from datetime import datetime

# 学术主题词库
ACADEMIC_THEMES = [
    "深度学习", "自然语言处理", "计算机视觉", "强化学习",
    "知识图谱", "量子计算", "边缘计算", "联邦学习",
    "生成式AI", "多模态学习", "图神经网络", "Transformer",
    "机器学习", "数据挖掘", "人工智能", "神经网络",
    "大语言模型", "推荐系统", "语音识别", "图像处理",
    "自动驾驶", "机器人", "生物医学", "金融风控",
    "文档智能", "代码生成", "智能问答", "语义搜索",
    "情感分析", "文本摘要", "机器翻译", "对话系统"
]

# 形容词词库
ADJECTIVES = [
    "智能", "先进", "创新", "专业", "学术", "研究",
    "高效", "精准", "深度", "全面", "前沿", "探索",
    "智慧", "卓越", "优化", "动态", "自适应", "自动化"
]

# 名词词库
NOUNS = [
    "知识库", "文档库", "数据集", "资料库", "信息库",
    "文献库", "论文库", "研究库", "案例库", "经验库"
]


def generate_academic_name() -> str:
    """生成学术风格名称: 主题_月份日期"""
    theme = random.choice(ACADEMIC_THEMES)
    timestamp = datetime.now().strftime("%m%d")
    return f"{theme}研究_{timestamp}"


def generate_random_name() -> str:
    """生成随机风格名称: 形容词+主题_随机ID"""
    adj = random.choice(ADJECTIVES)
    theme = random.choice(ACADEMIC_THEMES)
    random_id = ''.join(random.choices('0123456789abcdef', k=4))
    return f"{adj}{theme}_{random_id}"


def generate_timestamp_name() -> str:
    """生成时间戳风格名称: KB_年月日_时分秒"""
    return f"KB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def generate_simple_name() -> str:
    """生成简单风格名称: 主题_随机数字"""
    theme = random.choice(ACADEMIC_THEMES)
    random_num = random.randint(1000, 9999)
    return f"{theme}_{random_num}"


def generate_knowledge_base_name(style: str = "academic") -> str:
    """
    生成知识库名称

    Args:
        style: 命名风格，可选 "academic", "random", "timestamp", "simple"

    Returns:
        生成的知识库名称

    Raises:
        ValueError: 如果 style 不支持
    """
    generators = {
        "academic": generate_academic_name,
        "random": generate_random_name,
        "timestamp": generate_timestamp_name,
        "simple": generate_simple_name,
    }

    if style not in generators:
        raise ValueError(f"不支持的命名风格: {style}。支持的值: {list(generators.keys())}")

    return generators[style]()


def get_available_styles() -> list:
    """获取可用的命名风格列表"""
    return [
        {"value": "academic", "label": "学术风", "example": "深度学习研究_0311"},
        {"value": "random", "label": "随机风", "example": "智能文档库_a3f9"},
        {"value": "timestamp", "label": "时间戳", "example": "KB_20250311_143052"},
        {"value": "simple", "label": "简约风", "example": "自然语言处理_8472"},
    ]


if __name__ == "__main__":
    # 测试
    print("学术风:", generate_academic_name())
    print("随机风:", generate_random_name())
    print("时间戳:", generate_timestamp_name())
    print("简约风:", generate_simple_name())
    print("\n可用风格:")
    for style in get_available_styles():
        print(f"  {style['label']} ({style['value']}): {style['example']}")
