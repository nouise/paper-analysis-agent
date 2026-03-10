"""
日志工具 - 支持结构化日志和多种输出格式
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式"""

    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # 截断过长的消息
        if len(record.msg) > 500:
            record.msg = record.msg[:500] + "..."

        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON 结构化日志格式（用于生产环境）"""

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加额外字段
        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logger(
    name: str = 'project',
    log_file: str = 'project.log',
    level: int = logging.DEBUG,
    use_json: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置日志记录器

    Args:
        name: 日志器名称
        log_file: 日志文件名
        level: 日志级别
        use_json: 是否使用 JSON 格式（生产环境推荐）
        max_bytes: 单个日志文件最大字节数
        backup_count: 备份文件数量

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 防止重复配置
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False  # 防止重复输出

    # 创建日志目录
    log_dir = Path("output/log")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file_path = log_dir / log_file

    # 文件处理器（轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)

    if use_json:
        file_handler.setFormatter(JsonFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

    # 控制台处理器（带颜色）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    ))

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取已配置的日志器，如果不存在则创建默认配置"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        # 返回一个使用默认配置的日志器
        return setup_logger(name)
    return logger


class LogContext:
    """
    日志上下文管理器 - 添加上下文信息到所有日志

    示例:
        with LogContext(request_id="123", user_id="456"):
            logger.info("处理请求")  # 会自动包含 request_id 和 user_id
    """

    def __init__(self, **context):
        self.context = context
        self._old_factory = None

    def __enter__(self):
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        self._old_factory = old_factory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old_factory:
            logging.setLogRecordFactory(self._old_factory)


def log_execution_time(logger: Optional[logging.Logger] = None, level: int = logging.DEBUG):
    """
    装饰器 - 记录函数执行时间

    示例:
        @log_execution_time()
        async def my_function():
            ...
    """
    import time
    import functools

    def decorator(func):
        nonlocal logger
        logger = logger or logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                logger.log(level, f"[{func.__name__}] 执行时间: {elapsed:.3f}s")

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                logger.log(level, f"[{func.__name__}] 执行时间: {elapsed:.3f}s")

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# 确保在导入时 asyncio 可用
import asyncio
