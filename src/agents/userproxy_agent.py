"""
用户代理 - 支持 Web 的人工审核代理（请求隔离版）

解决了原全局单例模式的并发问题，每个请求使用独立的 agent 实例。
"""

import asyncio
import uuid
import weakref
from contextvars import ContextVar
from typing import Dict, Optional, List

from autogen_agentchat.agents import UserProxyAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)

# 存储每个请求的用户代理
_request_agents: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

# 当前请求 ID 的上下文变量
_request_id_var: ContextVar[str] = ContextVar('request_id', default='')


class UserInputTimeoutError(Exception):
    """用户输入超时错误"""
    pass


class WebUserProxyAgent(UserProxyAgent):
    """
    支持 Web 的人工审核代理

    每个请求创建独立实例，避免并发请求互相干扰。
    使用 Future 机制实现异步等待用户输入。
    """

    # 默认超时时间（秒）
    DEFAULT_TIMEOUT = 300.0  # 5分钟

    def __init__(self, name: str, request_id: str, timeout: float = DEFAULT_TIMEOUT):
        """
        初始化 Web 用户代理

        Args:
            name: 代理名称
            request_id: 请求唯一标识
            timeout: 等待用户输入的超时时间（秒）
        """
        super().__init__(name)
        self.request_id = request_id
        self.timeout = timeout
        self._waiting_future: Optional[asyncio.Future] = None
        self._is_waiting = False

        # 注册到全局字典
        _request_agents[request_id] = self
        logger.debug(f"[WebUserProxyAgent] 创建代理: request_id={request_id}")

    async def on_messages(
        self,
        messages: List[TextMessage],
        cancellation_token: CancellationToken
    ) -> TextMessage:
        """
        等待前端用户输入

        创建 Future 对象挂起协程，直到 set_user_input 被调用或超时。

        Args:
            messages: 来自其他代理的消息
            cancellation_token: 取消令牌

        Returns:
            包含用户输入的 TextMessage

        Raises:
            UserInputTimeoutError: 等待超时
            asyncio.CancelledError: 任务被取消
        """
        if self._is_waiting:
            logger.warning(f"[WebUserProxyAgent:{self.request_id}] 已经在等待输入")
            raise RuntimeError("已经在等待用户输入")

        self._waiting_future = asyncio.get_event_loop().create_future()
        self._is_waiting = True

        try:
            logger.info(f"[WebUserProxyAgent:{self.request_id}] 等待用户输入，超时={self.timeout}s")

            # 使用 wait_for 实现超时
            user_input = await asyncio.wait_for(
                self._waiting_future,
                timeout=self.timeout
            )

            logger.info(f"[WebUserProxyAgent:{self.request_id}] 收到用户输入")
            return TextMessage(content=user_input, source="human")

        except asyncio.TimeoutError:
            logger.warning(f"[WebUserProxyAgent:{self.request_id}] 等待用户输入超时")
            # 返回空对象，让工作流继续
            return TextMessage(content="{}", source="human")

        except asyncio.CancelledError:
            logger.info(f"[WebUserProxyAgent:{self.request_id}] 等待被取消")
            raise

        finally:
            self._is_waiting = False
            self._waiting_future = None

    def set_user_input(self, user_input: str) -> bool:
        """
        外部接口：接收前端输入并唤醒等待

        Args:
            user_input: 用户输入的内容

        Returns:
            是否成功设置结果
        """
        if self._waiting_future is None:
            logger.warning(f"[WebUserProxyAgent:{self.request_id}] 没有正在等待的 Future")
            return False

        if self._waiting_future.done():
            logger.warning(f"[WebUserProxyAgent:{self.request_id}] Future 已完成")
            return False

        try:
            self._waiting_future.set_result(user_input)
            logger.debug(f"[WebUserProxyAgent:{self.request_id}] 已设置用户输入")
            return True
        except Exception as e:
            logger.error(f"[WebUserProxyAgent:{self.request_id}] 设置用户输入失败: {e}")
            return False

    def cancel_wait(self) -> bool:
        """取消当前的等待"""
        if self._waiting_future and not self._waiting_future.done():
            self._waiting_future.cancel()
            return True
        return False

    def is_waiting(self) -> bool:
        """检查是否正在等待用户输入"""
        return self._is_waiting


def create_user_proxy_agent(
    request_id: Optional[str] = None,
    timeout: float = WebUserProxyAgent.DEFAULT_TIMEOUT
) -> WebUserProxyAgent:
    """
    创建新的用户代理实例

    Args:
        request_id: 请求 ID，如果为 None 则自动生成
        timeout: 超时时间

    Returns:
        新创建的 WebUserProxyAgent 实例
    """
    request_id = request_id or str(uuid.uuid4())
    return WebUserProxyAgent(
        name="user_proxy",
        request_id=request_id,
        timeout=timeout
    )


def get_user_proxy_agent(request_id: str) -> Optional[WebUserProxyAgent]:
    """
    根据 request_id 获取用户代理

    Args:
        request_id: 请求 ID

    Returns:
        用户代理实例，如果不存在则返回 None
    """
    return _request_agents.get(request_id)


def set_user_input_for_request(request_id: str, user_input: str) -> bool:
    """
    为指定请求设置用户输入

    Args:
        request_id: 请求 ID
        user_input: 用户输入内容

    Returns:
        是否成功设置
    """
    agent = get_user_proxy_agent(request_id)
    if agent is None:
        logger.error(f"未找到请求 {request_id} 的用户代理")
        return False
    return agent.set_user_input(user_input)


# ============================================
# 向后兼容：保留全局实例（仅用于单请求模式）
# ============================================

# 默认的全局实例（不推荐用于并发场景）
_default_user_proxy: Optional[WebUserProxyAgent] = None


def get_default_user_proxy() -> WebUserProxyAgent:
    """获取默认的全局用户代理（单请求模式使用）"""
    global _default_user_proxy
    if _default_user_proxy is None:
        _default_user_proxy = create_user_proxy_agent(request_id="default")
    return _default_user_proxy


# 为了向后兼容，保留 userProxyAgent 名称
userProxyAgent = get_default_user_proxy()
