"""
Paper-Agent 工作流编排器

使用 LangGraph StateGraph 串联: search → reading → analyse → writing → report
支持并发请求隔离，每个请求有独立的 orchestrator 实例。
"""

import asyncio
from typing import Optional, Dict, Any

from langgraph.graph import StateGraph, END, START

from src.core.state_models import (
    PaperAgentState, ExecutionState, NodeError,
    BackToFrontData, State, ConfigSchema
)
from src.nodes.search import search_node
from src.nodes.reading import reading_node
from src.nodes.analyse import analyse_node
from src.nodes.writing import writing_node
from src.nodes.report import report_node
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


class PaperAgentOrchestrator:
    """
    Paper-Agent 工作流编排器

    管理 LangGraph 工作流的生命周期，支持：
    - 请求隔离（每个请求独立实例）
    - 优雅取消
    - 状态追踪
    """

    def __init__(
        self,
        state_queue: asyncio.Queue,
        user_proxy: Optional[Any] = None,
        request_id: Optional[str] = None
    ):
        """
        初始化编排器

        Args:
            state_queue: 状态队列，用于向前端推送进度
            user_proxy: 用户代理实例（用于人工审核）
            request_id: 请求唯一标识
        """
        self.state_queue = state_queue
        self.user_proxy = user_proxy
        self.request_id = request_id or str(id(self))
        self.graph = self._build_graph()
        self._cancelled = False
        self._running = False

        logger.debug(f"[Orchestrator:{self.request_id}] 初始化完成")

    def _build_graph(self) -> StateGraph:
        """构建并编译 LangGraph 工作流"""
        builder = StateGraph(State, context_schema=ConfigSchema)

        # 添加节点
        builder.add_node("search_node", search_node)
        builder.add_node("reading_node", reading_node)
        builder.add_node("analyse_node", analyse_node)
        builder.add_node("writing_node", writing_node)
        builder.add_node("report_node", report_node)
        builder.add_node("handle_error_node", self.handle_error_node)

        # 设置入口点
        builder.set_entry_point("search_node")

        # 定义工作流路径
        builder.add_edge(START, "search_node")
        builder.add_conditional_edges("search_node", self.condition_handler)
        builder.add_conditional_edges("reading_node", self.condition_handler)
        builder.add_conditional_edges("analyse_node", self.condition_handler)
        builder.add_conditional_edges("writing_node", self.condition_handler)
        builder.add_conditional_edges("report_node", self.condition_handler)
        builder.add_edge("handle_error_node", END)

        return builder.compile()

    async def handle_error_node(self, state: State) -> State:
        """错误处理节点"""
        current_state = state["value"]
        current_state.current_step = ExecutionState.FAILED
        logger.error(
            f"[Orchestrator:{self.request_id}] 工作流失败 "
            f"at {current_state.current_step}: {current_state.error}"
        )
        return {"state_queue": state["state_queue"], "value": current_state}

    def condition_handler(self, state: State) -> str:
        """条件处理函数 - 决定工作流走向"""
        current_state = state["value"]
        err = current_state.error
        current_step = current_state.current_step

        # 根据当前步骤和错误状态决定下一步
        if current_step == ExecutionState.SEARCHING:
            if err.search_node_error:
                return "handle_error_node"
            return "reading_node"

        elif current_step == ExecutionState.READING:
            if err.reading_node_error:
                return "handle_error_node"
            return "analyse_node"

        elif current_step == ExecutionState.ANALYZING:
            if err.analyse_node_error:
                return "handle_error_node"
            return "writing_node"

        elif current_step == ExecutionState.WRITING:
            if err.writing_node_error:
                return "handle_error_node"
            return "report_node"

        elif current_step == ExecutionState.REPORTING:
            if err.report_node_error:
                return "handle_error_node"
            return END

        return "handle_error_node"

    async def run(
        self,
        user_request: str,
        max_papers: int = 10,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        执行完整工作流

        Args:
            user_request: 用户查询需求
            max_papers: 最大论文数量（默认 5 篇）
            config: 额外配置
        """
        if self._running:
            logger.warning(f"[Orchestrator:{self.request_id}] 已经在运行中")
            return

        self._running = True

        try:
            logger.info(
                f"[Orchestrator:{self.request_id}] "
                f"启动工作流: query='{user_request[:50]}...', max_papers={max_papers}"
            )

            # 初始化状态
            initial_state = PaperAgentState(
                user_request=user_request,
                max_papers=max_papers,
                error=NodeError(),
                config=config or {}
            )

            # 运行图
            await self.graph.ainvoke({
                "state_queue": self.state_queue,
                "value": initial_state
            })

            if self._cancelled:
                logger.info(f"[Orchestrator:{self.request_id}] 工作流已取消")
            else:
                logger.info(f"[Orchestrator:{self.request_id}] 工作流完成")

            # 发送完成信号
            await self.state_queue.put(BackToFrontData(
                step=ExecutionState.FINISHED,
                state="finished",
                data=None
            ))

        except asyncio.CancelledError:
            logger.info(f"[Orchestrator:{self.request_id}] 工作流被取消")
            await self.state_queue.put(BackToFrontData(
                step=ExecutionState.FAILED,
                state="cancelled",
                data="工作流已取消"
            ))
            raise

        except Exception as e:
            logger.error(f"[Orchestrator:{self.request_id}] 工作流异常: {e}")
            await self.state_queue.put(BackToFrontData(
                step=ExecutionState.FAILED,
                state="error",
                data=f"工作流异常: {str(e)}"
            ))
            raise

        finally:
            self._running = False

    async def cancel(self):
        """取消工作流"""
        if not self._running:
            return

        logger.info(f"[Orchestrator:{self.request_id}] 正在取消...")
        self._cancelled = True

        # 如果用户代理在等待输入，取消它
        if self.user_proxy and hasattr(self.user_proxy, 'cancel_wait'):
            self.user_proxy.cancel_wait()

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self._running

    def is_cancelled(self) -> bool:
        """检查是否已取消"""
        return self._cancelled


# 测试入口
if __name__ == "__main__":
    async def main():
        mock_queue = asyncio.Queue()
        orchestrator = PaperAgentOrchestrator(state_queue=mock_queue)
        await orchestrator.run("测试 Prompt")

    asyncio.run(main())
