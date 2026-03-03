import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录（agents目录）
src_parent_dir = os.path.dirname(os.path.dirname(current_dir))  # 向上两级找到 Paper-Agents 目录

# 将路径添加到 Python 搜索路径
sys.path.append(src_parent_dir)


from typing import Any, Dict, List, Optional, Union, AsyncGenerator, Sequence,get_type_hints,TypeAlias
from autogen_agentchat.agents import BaseChatAgent
import asyncio

from starlette.routing import Route
from src.utils.log_utils import setup_logger
from src.utils.tool_utils import handlerChunk
# 从 state_models 导入模型定义，保持类型一致
from src.core.state_models import ExtractedPapersData, ExtractedPaperData, KeyMethodology
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, TextMessage,StructuredMessage
from autogen_agentchat.base import Response
from autogen_core import CancellationToken, RoutedAgent
from src.agents.sub_analyse_agent.cluster_agent import PaperClusterAgent
from src.agents.sub_analyse_agent.deep_analyse_agent import DeepAnalyseAgent
from src.agents.sub_analyse_agent.global_analyse_agent import GlobalanalyseAgent
from src.core.model_client import create_default_client
from src.core.state_models import BackToFrontData
import json

from src.core.state_models import State,ExecutionState
from autogen_core import message_handler

logger = setup_logger(__name__)
# BaseChatAgent
class AnalyseAgent(BaseChatAgent):
    """基于AutoGen框架的论文分析智能体"""
    
    def __init__(self, name: str = "analyse_agent", state_queue: asyncio.Queue = None):
        super().__init__(name, "A simple agent that counts down.")
        """初始化论文分析系列智能体"""
        # 创建聚类智能体
        self.cluster_agent = PaperClusterAgent()
        # 创建深度分析智能体
        self.deep_analyse_agent = DeepAnalyseAgent()
        # 创建全局分析智能体
        self.global_analyse_agent = GlobalanalyseAgent()
    
        self.model_client = create_default_client()
        self.state_queue = state_queue
    
    @property
    def produced_message_types(self) -> Sequence[type[BaseChatMessage]]:
        return (TextMessage,)

    # @message_handler
    async def on_messages(self, messages: Sequence[BaseChatMessage], cancellation_token: CancellationToken) -> Response:
        """处理分析消息并返回响应
        
        Args:
            message: 提取的论文数据
            cancellation_token: 取消令牌
            
        Returns:
            Response: 包含分析结果的响应对象
        """
        # Calls the on_messages_stream.
        response: Response | None = None
        stream_message = messages[-1].content
        # async for msg in self.on_messages_stream(stream_message, cancellation_token):
        #     if isinstance(msg, Response):
        #         response = msg
        response = await self.on_messages_stream(stream_message, cancellation_token)
        assert response is not None
        return response

    # @message_handler
    async def on_messages_stream(self, message: ExtractedPapersData, cancellation_token: CancellationToken) -> Any:
        """流式处理分析消息
        
        Args:
            message: 提取的论文数据
            cancellation_token: 取消令牌
            
        Yields:
            生成分析过程中的事件或消息
            AsyncGenerator[BaseAgentEvent | BaseChatMessage | Response, None]
        """
        # 1. 调用聚类智能体进行论文聚类
        await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="thinking",data="正在进行论文聚类分析\n"))
        cluster_results = await self.cluster_agent.run(message)
        await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="thinking",data=f"论文聚类分析完成，共形成 {len(cluster_results)} 个聚类\n"))

        # 2. 调用深度分析智能体分析每个聚类的论文
        deep_analysis_results = []
        await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="thinking",data="正在进行论文深度分析\n"))
        deep_analysis_results = await asyncio.gather(*[self.deep_analyse_agent.run(cluster) for cluster in cluster_results])
        await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="thinking",data="论文深度分析完成\n"))
        
        # 3. 调用全局分析智能体生成整体分析报告
        await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="thinking",data="等待全局分析\n"))
        is_thinking = None
        async for chunk in self.global_analyse_agent.run(deep_analysis_results):
            if isinstance(chunk, Dict):
                if not chunk.get("isSuccess", False):
                    await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="error",data=chunk.get("global_analyse", "Unknown error")))
                    break
                global_analysis = chunk
                break
            state,is_thinking = handlerChunk(is_thinking,chunk)
            if state is None:
                continue
            await self.state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state=state,data=chunk))
            
        return Response(
            chat_message=TextMessage(
                content=json.dumps(global_analysis, ensure_ascii=False, indent=2),
                 source=self.name
            )
        )

    async def on_reset(self, cancellation_token: CancellationToken) -> None:
        pass
   
async def analyse_node(state: State) -> State:
    """搜索论文节点"""
    try:
        state_queue = state["state_queue"]
        current_state = state["value"]
        current_state.current_step = ExecutionState.ANALYZING
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="initializing",data=None))
        extracted_papers = current_state.extracted_data

        analyse_agent = AnalyseAgent(state_queue=state_queue)
        task = StructuredMessage(content=extracted_papers, source="User")
        # task = TextMessage(content=json.dumps(extracted_papers.model_dump(),ensure_ascii=False), source="User")
        response = await analyse_agent.run(task=task)

        analyse_results = response.messages[-1].content
        
        current_state.analyse_results = analyse_results
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="completed",data=analyse_results))

        return {"value": current_state}
            
    except Exception as e:
        err_msg = f"Analyse failed: {str(e)}"
        state["value"].error.analyse_node_error = err_msg
        await state_queue.put(BackToFrontData(step=ExecutionState.ANALYZING,state="error",data=err_msg))
        return state

async def main():
    """主函数 - 用于测试和调试"""
    from src.core.state_models import PaperAgentState, NodeError
    
    # 创建状态队列
    state_queue = asyncio.Queue()
    
    # 构造测试用的提取数据
    test_extracted_data = ExtractedPapersData(
        papers=[
            ExtractedPaperData(
                paper_id="paper_001",  # state_models 中需要 paper_id
                core_problem="如何提高深度学习模型在图像识别任务中的准确率和效率",
                key_methodology=KeyMethodology(
                    name="ResNet-50卷积神经网络",
                    principle="使用残差连接解决深度网络退化问题",
                    novelty="首次将残差学习应用于大规模图像分类任务"
                ),
                datasets_used=["ImageNet-1K (1.2M images)", "CIFAR-10"],
                evaluation_metrics=["Top-1 Accuracy", "Top-5 Accuracy", "F1-Score"],
                main_results="在ImageNet上Top-1准确率达到76.5%，比VGG-16提升3.2个百分点，训练速度提升40%",
                limitations="模型参数量较大（25.6M），在移动设备上部署困难；对小目标检测效果有限",
                contributions=[
                    "提出了残差学习框架，解决了深度网络训练困难的问题",
                    "在ImageNet数据集上取得了当时的最佳性能",
                    "为后续深度网络设计提供了重要思路"
                ]
            ),
            ExtractedPaperData(
                paper_id="paper_002",
                core_problem="如何让Transformer模型更好地理解自然语言的语义和上下文关系",
                key_methodology=KeyMethodology(
                    name="BERT预训练语言模型",
                    principle="通过双向Transformer编码器和掩码语言模型进行预训练",
                    novelty="首次提出双向预训练方法，同时考虑左右上下文信息"
                ),
                datasets_used=["BookCorpus (800M words)", "English Wikipedia (2.5B words)", "GLUE Benchmark"],
                evaluation_metrics=["Accuracy", "F1-Score", "GLUE Score"],
                main_results="在GLUE基准测试中获得80.5分，比GPT提升7.7分；在SQuAD 1.1问答任务上F1达到93.2%",
                limitations="预训练成本高昂，需要大量计算资源；模型推理速度较慢，不适合实时应用",
                contributions=[
                    "提出了双向预训练方法，显著提升了语言理解能力",
                    "在11个NLP任务上刷新了最佳记录",
                    "开源了预训练模型，推动了NLP领域的发展"
                ]
            )
        ]
    )
    
    # 初始化状态
    initial_state = PaperAgentState(
        user_request="帮我写一篇关于人工智能的调研报告",
        max_papers=2,
        error=NodeError(),
        config={},
        extracted_data=test_extracted_data  # 添加测试数据
    )
    
    state = {"state_queue": state_queue, "value": initial_state}
    
    # 运行分析节点
    result_state = await analyse_node(state)
    
    # 打印结果
    print("\n" + "="*50)
    print("分析完成！")
    print("="*50)
    if result_state["value"].analyse_results:
        print("\n分析结果:")
        print(result_state["value"].analyse_results)
    if result_state["value"].error.analyse_node_error:
        print("\n错误信息:")
        print(result_state["value"].error.analyse_node_error)
    
    return result_state

if __name__ == "__main__":
    print("开始调试 AnalyseAgent 模块...")
    print("-" * 50)
    asyncio.run(main())
