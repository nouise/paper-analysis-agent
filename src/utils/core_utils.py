"""
核心工具模块 - 缓存、指标收集、错误处理
"""

import asyncio
import hashlib
import json
import time
import logging
from contextlib import contextmanager
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================
# 缓存
# ============================================================

@dataclass
class CacheEntry(Generic[T]):
    """缓存条目"""
    value: T
    timestamp: float
    ttl: float


class SimpleCache:
    """简单的内存缓存，支持 TTL"""

    def __init__(self, default_ttl: float = 3600):
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = asyncio.Lock()

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """生成缓存键"""
        # 将参数转换为可哈希的形式
        try:
            key_data = json.dumps({
                'func': func_name,
                'args': [str(a) for a in args],
                'kwargs': {k: str(v) for k, v in sorted(kwargs.items())}
            }, sort_keys=True)
        except (TypeError, ValueError):
            # 如果无法序列化，使用字符串表示
            key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            # 检查是否过期
            if time.time() - entry.timestamp > entry.ttl:
                del self._cache[key]
                return None

            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """设置缓存值"""
        async with self._lock:
            self._cache[key] = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=ttl or self._default_ttl
            )

    async def clear(self):
        """清空缓存"""
        async with self._lock:
            self._cache.clear()

    async def clean_expired(self):
        """清理过期条目"""
        async with self._lock:
            now = time.time()
            expired_keys = [
                k for k, v in self._cache.items()
                if now - v.timestamp > v.ttl
            ]
            for k in expired_keys:
                del self._cache[k]
            return len(expired_keys)


# 全局缓存实例
_cache_instance: Optional[SimpleCache] = None


def get_cache() -> SimpleCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SimpleCache()
    return _cache_instance


def cache_result(ttl_seconds: float = 3600, key_func: Optional[Callable] = None):
    """
    缓存装饰器

    示例:
        @cache_result(ttl_seconds=1800)
        async def expensive_operation(param1, param2):
            ...
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache()

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(func.__name__, args, kwargs)

            # 尝试从缓存获取
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.debug(f"[Cache] Hit: {func.__name__}")
                return cached

            # 执行函数
            result = await func(*args, **kwargs)

            # 存入缓存
            await cache.set(cache_key, result, ttl_seconds)
            logger.debug(f"[Cache] Miss, cached: {func.__name__}")
            return result

        # 添加清除缓存的方法
        async_wrapper.cache_clear = cache.clear

        return async_wrapper
    return decorator


# ============================================================
# 性能监控
# ============================================================

@dataclass
class TimerStats:
    """计时统计"""
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0

    @property
    def avg_time(self) -> float:
        return self.total_time / self.count if self.count > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            'count': self.count,
            'avg_ms': round(self.avg_time * 1000, 2),
            'min_ms': round(self.min_time * 1000, 2) if self.min_time != float('inf') else 0,
            'max_ms': round(self.max_time * 1000, 2),
            'total_ms': round(self.total_time * 1000, 2),
        }


class MetricsCollector:
    """性能指标收集器（线程安全）"""

    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._timers: Dict[str, TimerStats] = defaultdict(TimerStats)
        self._errors: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def increment(self, name: str, value: int = 1):
        """增加计数器"""
        async with self._lock:
            self._counters[name] += value

    @contextmanager
    def timer(self, name: str):
        """计时上下文管理器"""
        start = time.perf_counter()
        try:
            yield
        except Exception as e:
            # 记录错误
            error_key = f"{name}_error"
            asyncio.create_task(self._record_error_async(error_key))
            raise
        finally:
            elapsed = time.perf_counter() - start
            asyncio.create_task(self._record_time_async(name, elapsed))

    async def _record_error_async(self, key: str):
        async with self._lock:
            self._errors[key] += 1

    async def _record_time_async(self, name: str, elapsed: float):
        async with self._lock:
            stats = self._timers[name]
            stats.count += 1
            stats.total_time += elapsed
            stats.min_time = min(stats.min_time, elapsed)
            stats.max_time = max(stats.max_time, elapsed)

    def get_summary(self) -> dict:
        """获取统计摘要"""
        return {
            'counters': dict(self._counters),
            'timers': {k: v.to_dict() for k, v in self._timers.items()},
            'errors': dict(self._errors),
        }

    def reset(self):
        """重置所有指标"""
        self._counters.clear()
        self._timers.clear()
        self._errors.clear()


# 全局指标收集器
_metrics_instance: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """获取全局指标收集器"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = MetricsCollector()
    return _metrics_instance


# ============================================================
# 错误处理
# ============================================================

class PaperAgentError(Exception):
    """Paper-Agent 基础异常"""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details,
        }


class PaperProcessingError(PaperAgentError):
    """论文处理错误"""

    def __init__(self, paper_id: str, paper_title: str, cause: Exception, **kwargs):
        super().__init__(
            message=f"处理论文失败 [{paper_id}] {paper_title}: {cause}",
            code="PAPER_PROCESSING_ERROR",
            details={
                'paper_id': paper_id,
                'paper_title': paper_title,
                'cause_type': type(cause).__name__,
                'cause_message': str(cause),
                **kwargs
            }
        )
        self.paper_id = paper_id
        self.paper_title = paper_title
        self.cause = cause


class LLMError(PaperAgentError):
    """LLM 调用错误"""

    def __init__(self, model: str, operation: str, cause: Exception, **kwargs):
        super().__init__(
            message=f"LLM 调用失败 [{model}] {operation}: {cause}",
            code="LLM_ERROR",
            details={
                'model': model,
                'operation': operation,
                'cause_type': type(cause).__name__,
                'cause_message': str(cause),
                **kwargs
            }
        )


class TimeoutError(PaperAgentError):
    """超时错误"""

    def __init__(self, operation: str, timeout: float, **kwargs):
        super().__init__(
            message=f"操作超时 [{operation}]: {timeout}s",
            code="TIMEOUT_ERROR",
            details={
                'operation': operation,
                'timeout': timeout,
                **kwargs
            }
        )


# ============================================================
# 重试工具
# ============================================================

@dataclass
class RetryConfig:
    """重试配置"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    retryable_exceptions: tuple = (Exception,)


async def retry_with_backoff(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    带指数退避的重试

    示例:
        result = await retry_with_backoff(
            some_async_function,
            arg1, arg2,
            config=RetryConfig(max_attempts=3, base_delay=2.0)
        )
    """
    config = config or RetryConfig()
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                logger.error(f"[Retry] 所有 {config.max_attempts} 次尝试失败: {e}")
                raise

            # 计算延迟时间（指数退避）
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )

            logger.warning(f"[Retry] 第 {attempt + 1} 次尝试失败: {e}, {delay:.1f}s 后重试...")
            await asyncio.sleep(delay)

    raise last_exception


# ============================================================
# 工具函数
# ============================================================

def truncate_string(s: Optional[str], max_length: int, suffix: str = "...") -> str:
    """截断字符串"""
    if s is None:
        return ""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def safe_json_loads(s: str, default: Any = None) -> Any:
    """安全的 JSON 解析"""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"JSON 解析失败: {e}")
        return default
