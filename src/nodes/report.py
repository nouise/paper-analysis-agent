"""
报告节点: 章节列表 → LLM整合 → 完整Markdown报告

流程:
  1. 接收所有写好的章节内容
  2. LLM 整合为连贯的完整报告
  3. 返回 Markdown 格式报告
  4. 自动保存报告到文件
"""

import os
import re
from datetime import datetime
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent

from src.core.model_client import create_report_model_client
from src.core.prompts import report_agent_prompt
from src.core.state_models import State, ExecutionState, BackToFrontData
from src.utils.log_utils import setup_logger

logger = setup_logger(__name__)


def save_report_to_file(report_content: str, user_request: str, output_dir: str = "output/reports") -> str:
    """保存报告到文件

    Args:
        report_content: 报告内容
        user_request: 用户查询
        output_dir: 输出目录

    Returns:
        保存的文件路径
    """
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 生成文件名：时间戳 + 查询关键词
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # 清理查询字符串，只保留字母数字和空格，然后转换为下划线
    clean_query = re.sub(r'[^\w\s-]', '', user_request)
    clean_query = re.sub(r'[-\s]+', '_', clean_query)
    clean_query = clean_query[:50]  # 限制长度

    filename = f"report_{timestamp}_{clean_query}.md"
    filepath = output_path / filename

    # 保存文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)

    logger.info(f"报告已保存到: {filepath}")
    return str(filepath)


async def report_node(state: State) -> State:
    """报告节点: 章节内容 → 完整Markdown报告"""
    state_queue = state["state_queue"]
    current_state = state["value"]
    current_state.current_step = ExecutionState.REPORTING
    await state_queue.put(BackToFrontData(step=ExecutionState.REPORTING, state="initializing"))

    try:
        sections = current_state.writted_sections
        sections_text = "\n\n---\n\n".join(sections) if sections else "无章节内容"

        # 创建独立 Agent
        model_client = create_report_model_client()
        agent = AssistantAgent(
            name="report_agent",
            model_client=model_client,
            system_message=report_agent_prompt,
        )

        prompt = f"""请将以下章节内容组装成完整的调研报告（Markdown格式）：

【章节内容开始】
{sections_text}
【章节内容结束】

【要求】
1. 使用Markdown格式排版
2. 补充必要的过渡语句
3. 保持专业学术风格
4. 直接输出报告"""

        print("📄 正在生成最终报告...")
        response = await agent.run(task=prompt)
        report_md = response.messages[-1].content
        print(f"✅ 报告生成完成 ({len(report_md)} 字)")

        # 保存报告到文件
        try:
            saved_path = save_report_to_file(report_md, current_state.user_request)
            print(f"💾 报告已保存到: {saved_path}")
        except Exception as save_error:
            logger.warning(f"保存报告失败: {save_error}")

        current_state.report_markdown = report_md
        await state_queue.put(BackToFrontData(
            step=ExecutionState.REPORTING,
            state="completed",
            data=report_md
        ))
        return {"value": current_state}

    except Exception as e:
        err_msg = f"Report failed: {e}"
        logger.error(err_msg)
        current_state.error.report_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.REPORTING, state="error", data=err_msg))
        return {"value": current_state}
