"""
搜索节点: 用户查询 → LLM提取关键词 → arXiv搜索 → 论文列表

流程:
  1. 用户输入自然语言查询
  2. LLM 将查询转换为结构化 SearchQuery (关键词 + 日期范围)
  3. 调用 arXiv API 获取论文元数据
  4. 返回论文列表
"""

import asyncio
import json
from typing import List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from pydantic import BaseModel, Field

from src.agents.userproxy_agent import get_user_proxy_agent
from src.core.prompts import search_agent_prompt
from src.core.model_client import create_search_model_client
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.tasks.paper_search import PaperSearcher
from src.utils.log_utils import setup_logger
from src.utils.core_utils import get_metrics

logger = setup_logger(__name__)
metrics = get_metrics()


# ============================================================
# 常量配置
# ============================================================

class SearchConfig:
    """搜索节点配置常量"""
    # 超时配置
    USER_REVIEW_TIMEOUT = 300.0  # 5分钟等待用户审核

    # 重试配置
    MAX_SEARCH_RETRIES = 2
    RETRY_DELAY = 2.0


# ============================================================
# 数据模型
# ============================================================

class SearchQuery(BaseModel):
    """LLM 输出的结构化搜索条件"""
    querys: List[str] = Field(description="英文检索关键词列表")
    start_date: Optional[str] = Field(default=None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="结束日期 YYYY-MM-DD")


# ============================================================
# 搜索节点
# ============================================================

async def search_node(state: State) -> State:
    """
    搜索节点: 用户查询 → 关键词 → arXiv论文列表

    Args:
        state: LangGraph 状态，包含 user_request 和配置

    Returns:
        更新后的状态，包含 search_results
    """
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.SEARCHING

    # 获取请求 ID（如果存在）
    request_id = current_state.config.get("request_id") if current_state.config else None

    await state_queue.put(BackToFrontData(
        step=ExecutionState.SEARCHING,
        state="initializing",
        summary="正在初始化搜索...",
        detail="准备搜索参数和连接...",
        data="正在初始化搜索...",
        progress=0
    ))

    with metrics.timer("search_node_total"):
        try:
            # 1. 创建 LLM Agent（每次调用新建，避免状态污染）
            model_client = create_search_model_client()
            search_agent = AssistantAgent(
                name="search_agent",
                model_client=model_client,
                system_message=search_agent_prompt,
                output_content_type=SearchQuery,
            )

            # 2. 让 LLM 提取搜索关键词
            prompt = f"请根据用户查询需求，生成检索查询条件。\n用户查询需求：{current_state.user_request}"

            response = await search_agent.run(task=prompt)
            search_query: SearchQuery = response.messages[-1].content

            logger.info(
                f"[Search] 关键词: {search_query.querys}, "
                f"时间: {search_query.start_date} ~ {search_query.end_date}"
            )
            print(f"[搜索] 搜索关键词: {search_query.querys}")
            print(f"[时间] 时间范围: {search_query.start_date} ~ {search_query.end_date}")

            # 3. 人工审核: 将关键词推送到前端，等待用户确认或修改
            review_data = json.dumps({
                "querys": search_query.querys,
                "start_date": search_query.start_date,
                "end_date": search_query.end_date
            }, ensure_ascii=False, indent=2)

            await state_queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="user_review",
                summary="等待用户审核搜索关键词",
                detail=review_data,
                data=review_data,  # 向后兼容
                collapsible=False  # 审核环节不允许折叠
            ))

            logger.info("[Search] 等待用户审核搜索关键词...")
            print("[等待] 等待用户审核搜索关键词...")

            # 挂起等待前端提交审核结果
            # 使用请求特定的 user_proxy 或默认的
            if request_id:
                user_proxy = get_user_proxy_agent(request_id)
                if user_proxy is None:
                    logger.warning(f"[Search] 未找到 request_id={request_id} 的用户代理，使用默认")
                    from src.agents.userproxy_agent import userProxyAgent
                    user_proxy = userProxyAgent
            else:
                from src.agents.userproxy_agent import userProxyAgent
                user_proxy = userProxyAgent

            review_result = await user_proxy.on_messages(
                [TextMessage(
                    content=f"请审核搜索关键词:\n{review_data}",
                    source="search_agent"
                )],
                cancellation_token=CancellationToken()
            )

            # 解析用户审核后的关键词
            user_input = review_result.content
            try:
                reviewed = json.loads(user_input)
                search_query = SearchQuery(
                    querys=reviewed.get("querys", search_query.querys),
                    start_date=reviewed.get("start_date", search_query.start_date),
                    end_date=reviewed.get("end_date", search_query.end_date)
                )
                logger.info(f"[Search] 用户审核后关键词: {search_query.querys}")
                print(f"[完成] 用户审核后关键词: {search_query.querys}")
                metrics.increment("search_user_review_success")
            except (json.JSONDecodeError, Exception) as parse_err:
                logger.warning(f"[Search] 无法解析用户审核输入: {parse_err}")
                print(f"[警告] 无法解析审核输入，使用LLM生成的原始关键词")
                metrics.increment("search_user_review_parse_failed")

            await state_queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="generating",
                summary="正在搜索论文...",
                detail=f"使用关键词: {', '.join(search_query.querys)}",
                data=f"正在使用关键词 {search_query.querys} 搜索论文...",
                progress=30
            ))

            # 4. 调用 arXiv API
            searcher = PaperSearcher()

            # 带重试的搜索
            results = []
            for attempt in range(SearchConfig.MAX_SEARCH_RETRIES):
                try:
                    results = await searcher.search_papers(
                        querys=search_query.querys,
                        max_results=current_state.max_papers,
                        start_date=search_query.start_date,
                        end_date=search_query.end_date,
                    )
                    break  # 成功则跳出循环
                except Exception as e:
                    logger.warning(f"[Search] 第 {attempt + 1} 次搜索失败: {e}")
                    if attempt < SearchConfig.MAX_SEARCH_RETRIES - 1:
                        await asyncio.sleep(SearchConfig.RETRY_DELAY)
                    else:
                        raise  # 最后一次失败则抛出异常

            print(f"[完成] 找到 {len(results)} 篇论文")
            logger.info(f"[Search] 找到 {len(results)} 篇论文")
            metrics.increment("papers_found", len(results))

            # 5. 更新状态
            current_state.search_results = results

            if len(results) == 0:
                current_state.error.search_node_error = "没有找到相关论文"
                await state_queue.put(BackToFrontData(
                    step=ExecutionState.SEARCHING,
                    state="error",
                    summary="未找到论文",
                    detail="未找到与查询相关的论文，请尝试修改关键词",
                    data="没有找到相关论文",
                    progress=100
                ))
                metrics.increment("search_no_results")
            else:
                await state_queue.put(BackToFrontData(
                    step=ExecutionState.SEARCHING,
                    state="completed",
                    summary=f"找到 {len(results)} 篇论文",
                    detail=f"使用关键词: {', '.join(search_query.querys)}\\n时间范围: {search_query.start_date or '无限制'} ~ {search_query.end_date or '无限制'}",
                    data=f"找到 {len(results)} 篇论文",
                    progress=100
                ))
                metrics.increment("search_success")

            return {"value": current_state}

        except Exception as e:
            err_msg = f"Search failed: {e}"
            logger.error(f"[Search] {err_msg}", exc_info=True)
            metrics.increment("search_errors")

            current_state.error.search_node_error = err_msg
            await state_queue.put(BackToFrontData(
                step=ExecutionState.SEARCHING,
                state="error",
                summary="搜索失败",
                detail=err_msg,
                data=err_msg,
                progress=100
            ))
            return {"value": current_state}
