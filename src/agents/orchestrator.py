"""
Paper-Agent 工作流编排器
使用 LangGraph StateGraph 串联: search → reading → analyse → writing → report
"""

from langgraph.graph import StateGraph, END, START
from src.core.state_models import PaperAgentState, ExecutionState, NodeError, BackToFrontData, State, ConfigSchema

# 从新的 nodes 模块导入各节点
from src.nodes.search import search_node
from src.nodes.reading import reading_node
from src.nodes.analyse import analyse_node
from src.nodes.writing import writing_node
from src.nodes.report import report_node

import asyncio


class PaperAgentOrchestrator:
    def __init__(self,state_queue):
        self.state_queue = state_queue
        self.graph = self._build_graph()

    async def handle_error_node(self, state: State) -> State:
        """错误处理节点"""
        current_state = state["value"]
        current_state.current_step = ExecutionState.FAILED
        print(f"Workflow failed at {current_state.current_step}: {current_state.error}")
        return {"state_queue": state["state_queue"], "value": current_state}

    def condition_handler(self, state: State) -> str:
        """条件处理函数"""
        # 如果state.get("error") is not None那么就返回到handle_error_node
        current_state = state["value"]
        err = current_state.error
        current_step = current_state.current_step
        if err.search_node_error is None and current_step == ExecutionState.SEARCHING:
            return "reading_node"
        elif err.reading_node_error is None and current_step == ExecutionState.READING:
            return "analyse_node"
        elif err.analyse_node_error is None and current_step == ExecutionState.ANALYZING:
            return "writing_node"
        elif err.writing_node_error is None and current_step == ExecutionState.WRITING:
            return "report_node"
        elif err.report_node_error is None and current_step == ExecutionState.REPORTING:
            return END
        else:
            return "handle_error_node"


    def _build_graph(self):
        """构建并编译LangGraph工作流"""
        builder = StateGraph(State, context_schema=ConfigSchema)
        
        # 添加节点
        builder.add_node("search_node", search_node)
        builder.add_node("reading_node", reading_node)
        builder.add_node("analyse_node", analyse_node)
        builder.add_node("writing_node", writing_node)
        builder.add_node("report_node", report_node)
        builder.add_node("handle_error_node", self.handle_error_node)

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
    

    
    async def run(self, user_request: str, max_papers: int = 5):
        """执行完整工作流
        
        参数:
            user_request: 用户查询需求
            max_papers: 最大论文数量（默认50篇）
                       - 可通过命令行参数 --max-papers 修改
                       - 例如: --max-papers 10 表示最多搜索10篇论文
        """
        # 初始化状态
        # await self.state_queue.put(BackToFrontData(step="start",state="processing",data=None))
        print(f"Starting workflow... (max_papers={max_papers})")
        initial_state = PaperAgentState(
            user_request=user_request,
            max_papers=max_papers,
            error=NodeError(),
            config={}  # 可以传入各种配置
        )
        print("Initial state created.")
        # 运行图
        await self.graph.ainvoke({"state_queue": self.state_queue, "value": initial_state})
        print("Workflow completed.")
        await self.state_queue.put(BackToFrontData(step=ExecutionState.FINISHED,state="finished",data=None))

    

if __name__ == "__main__":
    # 创建一个模拟队列
    mock_queue = asyncio.Queue() 
    orchestrator = PaperAgentOrchestrator(state_queue=mock_queue)
    # 使用 asyncio.run 运行异步主函数
    asyncio.run(orchestrator.run("测试Prompt"))

    