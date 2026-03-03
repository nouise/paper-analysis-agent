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
from pydantic import BaseModel, Field
from typing import Optional, List

from autogen_agentchat.agents import AssistantAgent

from src.core.prompts import search_agent_prompt
from src.core.model_client import create_search_model_client
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.tasks.paper_search import PaperSearcher
from src.agents.userproxy_agent import userProxyAgent
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


# ============================================================
# 搜索查询结构
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
    """搜索节点: 用户查询 → 关键词 → arXiv论文列表"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.SEARCHING
    await state_queue.put(BackToFrontData(step=ExecutionState.SEARCHING, state="initializing"))

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

        logger.info(f"搜索关键词: {search_query.querys}, 时间: {search_query.start_date} ~ {search_query.end_date}")
        print(f"🔍 搜索关键词: {search_query.querys}")
        print(f"📅 时间范围: {search_query.start_date} ~ {search_query.end_date}")

        # 3. 人工审核: 将关键词推送到前端，等待用户确认或修改
        review_data = json.dumps({
            "querys": search_query.querys,
            "start_date": search_query.start_date,
            "end_date": search_query.end_date
        }, ensure_ascii=False, indent=2)
        await state_queue.put(BackToFrontData(
            step=ExecutionState.SEARCHING,
            state="user_review",
            data=review_data
        ))
        logger.info("等待用户审核搜索关键词...")
        print("⏳ 等待用户审核搜索关键词...")

        # 挂起等待前端提交审核结果
        from autogen_agentchat.messages import TextMessage
        from autogen_core import CancellationToken
        review_result = await userProxyAgent.on_messages(
            [TextMessage(content=f"请审核搜索关键词:\n{review_data}", source="search_agent")],
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
            logger.info(f"用户审核后关键词: {search_query.querys}")
            print(f"✅ 用户审核后关键词: {search_query.querys}")
        except (json.JSONDecodeError, Exception) as parse_err:
            logger.warning(f"无法解析用户审核输入为JSON，使用原始关键词: {parse_err}")
            print(f"⚠️ 无法解析审核输入，使用LLM生成的原始关键词")

        await state_queue.put(BackToFrontData(
            step=ExecutionState.SEARCHING,
            state="generating",
            data=f"正在使用关键词 {search_query.querys} 搜索论文..."
        ))

        # 4. 调用 arXiv API
        searcher = PaperSearcher()
        results = await searcher.search_papers(
            querys=search_query.querys,
            max_results=current_state.max_papers,
            start_date=search_query.start_date,
            end_date=search_query.end_date,
        )
        print(f"✅ 找到 {len(results)} 篇论文")

        # 5. 更新状态
        current_state.search_results = results
        if len(results) == 0:
            current_state.error.search_node_error = "没有找到相关论文"
            await state_queue.put(BackToFrontData(step=ExecutionState.SEARCHING, state="error", data="没有找到相关论文"))
        else:
            await state_queue.put(BackToFrontData(step=ExecutionState.SEARCHING, state="completed", data=f"找到 {len(results)} 篇论文"))

        return {"value": current_state}

    except Exception as e:
        err_msg = f"Search failed: {e}"
        logger.error(err_msg)
        current_state.error.search_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.SEARCHING, state="error", data=err_msg))
        return {"value": current_state}
