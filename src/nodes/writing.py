"""
写作节点: 全局分析 → 大纲拆分 → 并行章节写作 → 章节列表

流程:
  1. Writing Director: 根据分析结果生成写作大纲
  2. 并行写作: 对每个章节独立调用 LLM 写作（支持流式输出）
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
# 流式写作支持
# ============================================================

async def _stream_write_section(
    section: str,
    index: int,
    user_request: str,
    global_analysis: str,
    state_queue: asyncio.Queue,
) -> str:
    """流式写作单个章节，带 review 和优化循环，实时推送内容片段"""
    try:
        model_client = create_subwriting_writing_model_client()

        # 第一轮：初始写作
        await state_queue.put(BackToFrontData(
            step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
            state="generating",
            summary=f"Writing section {index + 1}: {section[:50]}...",
            progress=0,
            stream_content=f"\n### 章节 {index + 1}: {section}\n\n"
        ))

        # 初始写作
        writing_agent = AssistantAgent(
            name="writing_agent",
            model_client=model_client,
            system_message=writing_agent_prompt,
        )

        task_prompt = f"""请完成以下写作任务：
用户请求：{user_request}
当前章节任务：{section}
全局分析参考：{global_analysis[:2000]}

请开始写作："""

        result = await writing_agent.run(task=task_prompt)
        content = result.messages[-1].content if result.messages else ""

        # 流式推送初始内容
        chunk_size = 100
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            await state_queue.put(BackToFrontData(
                step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                state="generating",
                summary=f"Writing section {index + 1} (Draft 1)",
                progress=min(50, int((i + len(chunk)) / len(content) * 50)) if content else 25,
                stream_content=chunk
            ))
            await asyncio.sleep(0.02)

        # Review 和优化循环
        max_iterations = 2
        current_iteration = 1

        while current_iteration <= max_iterations:
            # Review 阶段
            await state_queue.put(BackToFrontData(
                step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                state="thinking",
                summary=f"Reviewing section {index + 1} (Draft {current_iteration})",
                progress=50 + (current_iteration - 1) * 25,
                stream_content=f"\n\n---\n**[Review Phase {current_iteration}]**\n\n"
            ))

            review_agent = AssistantAgent(
                name="review_agent",
                model_client=create_default_client(),
                system_message=review_agent_prompt,
            )

            review_prompt = f"""请审查以下章节内容：

章节任务：{section}

当前内容：
{content}

请提供：
1. 内容质量评分 (1-10)
2. 主要问题和改进建议
3. 是否需要重写 (如果评分 < 7，请说 "需要重写")

审查意见："""

            review_result = await review_agent.run(task=review_prompt)
            review_feedback = review_result.messages[-1].content if review_result.messages else "APPROVE"

            # 推送 review 结果到前端
            await state_queue.put(BackToFrontData(
                step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                state="thinking",
                summary=f"Review feedback for section {index + 1}",
                progress=50 + (current_iteration - 1) * 25 + 12,
                stream_content=f"**Review Feedback:**\n{review_feedback}\n\n"
            ))

            # 检查是否需要继续优化
            if "APPROVE" in review_feedback.upper() or "需要重写" not in review_feedback:
                await state_queue.put(BackToFrontData(
                    step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                    state="thinking",
                    summary=f"Section {index + 1} approved",
                    progress=75 + (current_iteration - 1) * 12,
                    stream_content=f"\n✅ **Approved** - 内容通过审查\n\n"
                ))
                break

            # 需要优化，进行下一轮写作
            if current_iteration < max_iterations:
                await state_queue.put(BackToFrontData(
                    step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                    state="generating",
                    summary=f"Optimizing section {index + 1} (Draft {current_iteration + 1})",
                    progress=50 + current_iteration * 25,
                    stream_content=f"\n\n**[Optimization Phase {current_iteration}]**\n\n"
                ))

                # 根据 review 反馈优化
                optimize_prompt = f"""请根据审查意见优化以下内容：

章节任务：{section}

当前内容：
{content}

审查意见：
{review_feedback}

请输出优化后的内容："""

                optimize_result = await writing_agent.run(task=optimize_prompt)
                content = optimize_result.messages[-1].content if optimize_result.messages else content

                # 推送优化后的内容
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    await state_queue.put(BackToFrontData(
                        step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
                        state="generating",
                        summary=f"Optimizing section {index + 1}",
                        progress=50 + current_iteration * 25 + int((i + len(chunk)) / len(content) * 12) if content else 60,
                        stream_content=chunk
                    ))
                    await asyncio.sleep(0.02)

            current_iteration += 1

        # 发送完成状态
        await state_queue.put(BackToFrontData(
            step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
            state="completed",
            summary=f"Section {index + 1} completed",
            progress=100,
            stream_content=f"\n\n---\n**Section {index + 1} Final** ✅\n\n"
        ))

        return content

    except Exception as e:
        logger.error(f"章节 {index} 流式写作失败: {e}")
        await state_queue.put(BackToFrontData(
            step=f"{ExecutionState.SECTION_WRITING}_{index + 1}",
            state="error",
            summary=f"Section {index + 1} failed",
            detail=str(e)
        ))
        return f"章节 {section} 写作失败: {e}"


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

        # Step 2: 并行写作（限制并发避免 API 过载，支持流式输出）
        print(f"\n[编辑] 开始并行写作 {len(sections)} 个章节（支持流式输出）...")
        semaphore = asyncio.Semaphore(2)  # 最多2个章节同时写

        async def _write_with_semaphore(section, idx):
            async with semaphore:
                content = await _stream_write_section(
                    section, idx, user_request, global_analysis, state_queue
                )
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
