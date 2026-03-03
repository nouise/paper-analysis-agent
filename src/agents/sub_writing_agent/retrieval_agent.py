from autogen_agentchat.agents import AssistantAgent
from src.core.model_client import create_default_client
from autogen_core.tools import FunctionTool
from src.services.retrieval_tool import retrieval_tool
from src.core.prompts import retrieval_agent_prompt

def create_retrieval_agent(state_queue=None):
    model_client = create_default_client()

    retriever = FunctionTool(retrieval_tool, description="用于从本地知识库中查询外部资料，来辅助写作的工具")

    retrieval_agent = AssistantAgent(
        name="retrieval_agent",
        description="一个检索助手，负责根据条件从本地知识库中查询外部资料。",
        model_client=model_client,
        system_message=retrieval_agent_prompt,
        tools=[retriever],
        reflect_on_tool_use=False,
    )
    return retrieval_agent
