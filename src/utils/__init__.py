"""
工具模块 - 通用工具函数

提供:
- 哈希工具
- PDF 处理
- 日志工具导出
- 核心工具导出（缓存、指标、错误处理）
"""

import hashlib
import os
import time
from typing import Optional

from src.utils.log_utils import setup_logger

# 导出核心工具
from src.utils.core_utils import (
    # 缓存
    SimpleCache,
    get_cache,
    cache_result,

    # 指标
    MetricsCollector,
    get_metrics,

    # 错误处理
    PaperAgentError,
    PaperProcessingError,
    LLMError,
    TimeoutError,

    # 重试工具
    RetryConfig,
    retry_with_backoff,

    # 工具函数
    truncate_string,
    safe_json_loads,
)

logger = setup_logger(__name__)


# ============================================================
# PDF 处理
# ============================================================

def is_text_pdf(pdf_path: str) -> bool:
    """
    检查 PDF 是否为文本型（非扫描型）

    Args:
        pdf_path: PDF 文件路径

    Returns:
        如果超过 50% 的页面有文本内容则返回 True
    """
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if total_pages == 0:
            return False

        text_pages = 0
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                text_pages += 1

        text_ratio = text_pages / total_pages
        return text_ratio > 0.5

    except Exception as e:
        logger.error(f"检查 PDF 类型失败: {e}")
        return False


# ============================================================
# 哈希工具
# ============================================================

def hashstr(
    input_string: str,
    length: Optional[int] = None,
    with_salt: bool = False
) -> str:
    """
    生成字符串的 MD5 哈希值

    Args:
        input_string: 输入字符串
        length: 截取长度，默认为 None 表示不截取
        with_salt: 是否加盐（使用时间戳）

    Returns:
        哈希字符串
    """
    try:
        encoded_string = str(input_string).encode("utf-8")
    except UnicodeEncodeError:
        encoded_string = str(input_string).encode("utf-8", errors="replace")

    if with_salt:
        salt = str(time.time())
        encoded_string = (encoded_string.decode("utf-8") + salt).encode("utf-8")

    hash_value = hashlib.md5(encoded_string).hexdigest()

    if length:
        return hash_value[:length]
    return hash_value


def hash_file(filepath: str, algorithm: str = "md5") -> str:
    """
    计算文件的哈希值

    Args:
        filepath: 文件路径
        algorithm: 哈希算法（md5, sha256）

    Returns:
        哈希字符串
    """
    hasher = hashlib.new(algorithm)

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


# ============================================================
# 路径处理
# ============================================================

def ensure_dir(path: str) -> str:
    """
    确保目录存在，如果不存在则创建

    Args:
        path: 目录路径

    Returns:
        目录路径
    """
    os.makedirs(path, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名（移除非法字符）

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    import re
    # 移除外号字符
    safe = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    safe = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe)
    # 限制长度
    return safe[:255]


# ============================================================
# 导出
# ============================================================

__all__ = [
    # 原始工具
    'is_text_pdf',
    'hashstr',
    'hash_file',
    'ensure_dir',
    'safe_filename',
    'setup_logger',

    # 缓存
    'SimpleCache',
    'get_cache',
    'cache_result',

    # 指标
    'MetricsCollector',
    'get_metrics',

    # 错误
    'PaperAgentError',
    'PaperProcessingError',
    'LLMError',
    'TimeoutError',

    # 重试
    'RetryConfig',
    'retry_with_backoff',

    # 工具
    'truncate_string',
    'safe_json_loads',
]
