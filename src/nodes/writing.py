"""
写作节点: 全局分析 → 大纲拆分 → 并行章节写作 → 章节列表

流程:
  1. Writing Director: 根据分析结果生成写作大纲
  2. 并行写作: 对每个章节独立调用 LLM 写作
  3. 返回写完的章节列表
"""

import asyncio
import re
import json
from typing import List, Dict, Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_core.tools import FunctionTool

from src.core.model_client import (
    create_default_client,
    create_subwriting_writing_director_model_client,
    create_subwriting_writing_model_client,
)
from src.core.prompts import (
    writing_director_agent_prompt,
    writing_agent_prompt,
    review_agent_prompt,
    retrieval_agent_prompt,
    selector_prompt,
)
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.services.retrieval_tool import retrieval_tool
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


# ============================================================
# 1. 写作主管: 生成大纲 → 拆分章节
# ============================================================

def _parse_outline(outline_str: str) -> List[str]:
    """将大纲文本解析为章节列表"""
    sections = re.split(r'(\d+\.\d+|\d+)\s', outline_str.strip())
    result = []
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            section = f"{sections[i].strip()} {sections[i + 1].strip()}"
            result.append(section)
    # 如果没匹配到，按行拆分
    if not result:
        result = [line.strip() for line in outline_str.strip().split('\n') if line.strip()]
    return result


async def _generate_outline(user_request: str, global_analysis: str) -> List[str]:
    """让 LLM 生成写作大纲并拆分为章节列表"""
    model_client = create_subwriting_writing_director_model_client()
    director = AssistantAgent(
        name="writing_director",
        model_client=model_client,
        system_message=writing_director_agent_prompt,
    )

    prompt = f"""用户的需求: {user_request}
该领域的分析: {global_analysis}
请生成写作子任务："""

    response = await director.run(task=prompt)
    outline_text = response.messages[-1].content
    sections = _parse_outline(outline_text)
    return sections


# ============================================================
# 2. 章节写作: 每个章节独立调用 LLM
# ============================================================

async def _write_one_section(
    section: str,
    index: int,
    user_request: str,
    global_analysis: str,
) -> str:
    """写作单个章节"""
    try:
        model_client = create_subwriting_writing_model_client()
        
        # 创建写作 Agent
        writing_agent = AssistantAgent(
            name="writing_agent",
            model_client=model_client,
            system_message=writing_agent_prompt,
        )
        
        # 创建检索 Agent (with retrieval tool)
        retriever_tool = FunctionTool(retrieval_tool, description="从知识库检索相关文献资料")
        retrieval_agent = AssistantAgent(
            name="retrieval_agent",
            model_client=create_default_client(),
            system_message=retrieval_agent_prompt,
            tools=[retriever_tool],
            reflect_on_tool_use=False,
        )
        
        # 创建审查 Agent
        review_agent = AssistantAgent(
            name="review_agent",
            model_client=create_default_client(),
            system_message=review_agent_prompt,
        )

        # 使用 SelectorGroupChat 进行多轮协作
        termination = TextMentionTermination("APPROVE")
        selector_client = create_default_client()
        
        group = SelectorGroupChat(
            [writing_agent, retrieval_agent, review_agent],
            model_client=selector_client,
            termination_condition=termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=False,
        )

        task_prompt = f"""请完成以下写作任务：
用户请求：{user_request}
当前章节任务：{section}
全局分析参考：{global_analysis[:2000]}

请开始写作："""

        result = await group.run(task=task_prompt)
        
        # 提取写作 Agent 的最终输出
        for msg in reversed(result.messages):
            if msg.source == "writing_agent" and hasattr(msg, 'content') and isinstance(msg.content, str):
                return msg.content
        
        # 如果没找到 writing_agent 的输出，取最后的文本
        return result.messages[-1].content if result.messages else f"章节 {section} 写作失败"

    except Exception as e:
        logger.error(f"章节 {index} 写作失败: {e}")
        return f"章节 {section} 写作失败: {e}"


# ============================================================
# 写作节点入口
# ============================================================

async def writing_node(state: State) -> State:
    """写作节点: 生成大纲 → 并行写作各章节"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.WRITING
    await state_queue.put(BackToFrontData(step=ExecutionState.WRITING, state="initializing"))

    try:
        user_request = current_state.user_request
        global_analysis = current_state.analyse_results or ""

        # Step 1: 生成大纲
        print("[写作] 正在生成写作大纲...")
        await state_queue.put(BackToFrontData(step=ExecutionState.WRITING_DIRECTOR, state="initializing"))
        sections = await _generate_outline(user_request, global_analysis)
        print(f"[大纲] 大纲包含 {len(sections)} 个章节:")
        for i, s in enumerate(sections):
            print(f"  {i + 1}. {s[:60]}...")
        await state_queue.put(BackToFrontData(step=ExecutionState.WRITING_DIRECTOR, state="completed"))

        # Step 2: 并行写作（限制并发避免 API 过载）
        print(f"\n[编辑] 开始并行写作 {len(sections)} 个章节...")
        semaphore = asyncio.Semaphore(2)  # 最多2个章节同时写

        async def _write_with_semaphore(section, idx):
            async with semaphore:
                await state_queue.put(BackToFrontData(
                    step=f"{ExecutionState.SECTION_WRITING}_{idx + 1}", state="initializing"
                ))
                content = await _write_one_section(section, idx, user_request, global_analysis)
                await state_queue.put(BackToFrontData(
                    step=f"{ExecutionState.SECTION_WRITING}_{idx + 1}", state="completed"
                ))
                print(f"  [完成] 章节 {idx + 1} 写作完成 ({len(content)} 字)")
                return content

        tasks = [_write_with_semaphore(s, i) for i, s in enumerate(sections)]
        written = await asyncio.gather(*tasks, return_exceptions=True)

        # 收集结果
        written_sections = []
        for i, result in enumerate(written):
            if isinstance(result, Exception):
                logger.error(f"章节 {i + 1} 写作异常: {result}")
                written_sections.append(f"## 章节 {i + 1}\n\n写作失败: {result}")
            else:
                written_sections.append(result)

        current_state.writted_sections = written_sections
        await state_queue.put(BackToFrontData(step=ExecutionState.WRITING, state="completed",
                                               data=f"写作完成，共 {len(written_sections)} 个章节"))
        return {"value": current_state}

    except Exception as e:
        err_msg = f"Writing failed: {e}"
        logger.error(err_msg)
        current_state.error.writing_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.WRITING, state="error", data=err_msg))
        return {"value": current_state}
