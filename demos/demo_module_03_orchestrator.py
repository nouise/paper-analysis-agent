"""
模块 3: LangGraph 工作流编排演示
可以独立运行，展示工作流设计和节点编排能力
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_orchestrator():
    """演示编排器"""
    print("=" * 60)
    print("模块 3.1: LangGraph 工作流编排 (agents/orchestrator.py)")
    print("=" * 60)

    from src.agents.orchestrator import PaperAgentOrchestrator
    from src.core.state_models import ExecutionState

    # 展示编排器结构
    print("\n🔄 工作流图结构:")
    print("""
    START → search_node → reading_node → analyse_node → writing_node → report_node → END
                ↓               ↓              ↓               ↓               ↓
           handle_error_node ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
    """)

    # 展示节点映射
    print("📋 节点职责:")
    nodes = {
        "search_node": "LLM提取关键词 → arXiv搜索 → 人工审核 → 返回论文列表",
        "reading_node": "批量下载论文PDF → 解析内容 → 提取结构化数据",
        "analyse_node": "KMeans聚类 → 深度分析 → 综合分析",
        "writing_node": "SelectorGroupChat多代理协作写作",
        "report_node": "整合章节 → 生成Markdown报告",
        "handle_error_node": "统一错误处理",
    }
    for node, desc in nodes.items():
        print(f"  {node}:")
        print(f"    {desc}")

    # 展示条件路由逻辑
    print("\n🔀 条件路由逻辑:")
    print("  每个节点执行后检查:")
    print("    if error.node_error: -> handle_error_node")
    print("    else: -> next_node")

    # 创建编排器实例（不运行）
    print("\n🏗️  创建编排器实例:")
    mock_queue = asyncio.Queue()
    orchestrator = PaperAgentOrchestrator(
        state_queue=mock_queue,
        request_id="demo-001"
    )
    print(f"  ✓ 编排器创建成功")
    print(f"  请求ID: {orchestrator.request_id}")
    print(f"  是否运行中: {orchestrator.is_running()}")

    # 展示执行状态枚举
    print("\n📊 执行状态定义:")
    for state in ExecutionState:
        print(f"  - {state.value}")

    print("\n✅ 编排器演示完成")
    return True


def demo_nodes():
    """演示各个节点"""
    print("\n" + "=" * 60)
    print("模块 3.2: 工作流节点 (nodes/)")
    print("=" * 60)

    # Search Node
    print("\n🔍 Search Node (nodes/search.py):")
    print("""
    流程:
      1. 创建 AssistantAgent (结构化输出)
      2. LLM 提取搜索关键词 (SearchQuery)
      3. 推送审核请求到前端 (user_review)
      4. 等待 UserProxyAgent 返回审核结果
      5. 调用 PaperSearcher 搜索 arXiv
      6. 返回论文列表

    关键代码:
      search_agent = AssistantAgent(
          name="search_agent",
          output_content_type=SearchQuery,  # 结构化输出
      )
      review_result = await user_proxy.on_messages(...)  # 人工介入
    """)

    # Reading Node
    print("\n📖 Reading Node (nodes/reading.py):")
    print("""
    流程:
      1. 并行下载所有论文 PDF (asyncio.gather)
      2. 解析 PDF 提取文本
      3. 使用 LLM 提取结构化信息
      4. 存储到临时知识库

    输出:
      ExtractedPapersData: 包含每篇论文的核心问题、方法、结果等
    """)

    # Analyse Node
    print("\n📊 Analyse Node (nodes/analyse.py):")
    print("""
    流程:
      1. Cluster Agent: KMeans 聚类 + LLM 主题命名
      2. Deep Analyse Agent: 每聚类深度分析
      3. Global Analyse Agent: 跨聚类综合分析

    涉及代理:
      - sub_analyse_agent/cluster_agent.py
      - sub_analyse_agent/deep_analyse_agent.py
      - sub_analyse_agent/global_analyse_agent.py
    """)

    # Writing Node
    print("\n✍️  Writing Node (nodes/writing.py):")
    print("""
    流程:
      1. Writing Director: 生成章节大纲
      2. SelectorGroupChat 协作写作:
         - Writing Agent: 撰写章节
         - Retrieval Agent: RAG 检索
         - Review Agent: 质量审核
      3. 整合所有章节

    终止条件:
      Review Agent 输出 "APPROVE"
    """)

    # Report Node
    print("\n📄 Report Node (nodes/report.py):")
    print("""
    流程:
      1. 整合所有章节内容
      2. 添加报告元数据
      3. 保存为 Markdown 文件
      4. 可选: 转换为 WeChat HTML
    """)

    print("\n✅ 节点演示完成")
    return True


def demo_state_flow():
    """演示状态流转"""
    print("\n" + "=" * 60)
    print("模块 3.3: 状态流转示例")
    print("=" * 60)

    from src.core.state_models import PaperAgentState, ExecutionState, NodeError

    print("\n🔄 状态流转示例:")

    # 创建初始状态
    state = PaperAgentState(
        user_request="分析 Transformer 在医学图像的应用",
        max_papers=5
    )

    print(f"\n  初始状态:")
    print(f"    current_step: {state.current_step.value}")
    print(f"    user_request: {state.user_request}")

    # 模拟状态流转
    steps = [
        ExecutionState.SEARCHING,
        ExecutionState.READING,
        ExecutionState.ANALYZING,
        ExecutionState.WRITING,
        ExecutionState.REPORTING,
        ExecutionState.COMPLETED,
    ]

    for step in steps:
        state.current_step = step
        print(f"\n  -> 流转到: {step.value}")

        # 模拟填充数据
        if step == ExecutionState.SEARCHING:
            state.search_results = [{"title": f"论文{i}", "id": f"id{i}"} for i in range(3)]
            print(f"      search_results: {len(state.search_results)} 篇论文")

        elif step == ExecutionState.READING:
            print(f"      extracted_data: 已提取结构化数据")

        elif step == ExecutionState.ANALYZING:
            state.analyse_results = '{"clusters": 3, "topics": ["A", "B", "C"]}'
            print(f"      analyse_results: 聚类分析完成")

        elif step == ExecutionState.WRITING:
            state.writted_sections = ["引言", "方法", "结果", "讨论"]
            print(f"      writted_sections: {len(state.writted_sections)} 个章节")

        elif step == ExecutionState.REPORTING:
            state.report_markdown = "# 研究报告\n\n这是生成的报告..."
            print(f"      report_markdown: 已生成 ({len(state.report_markdown)} 字符)")

    print("\n✅ 状态流转演示完成")
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("模块 3: LangGraph 工作流编排演示")
    print("=" * 60)
    print("\n包含:")
    print("  - 编排器 (agents/orchestrator.py)")
    print("  - 工作流节点 (nodes/)")
    print("  - 状态流转")

    try:
        demo_orchestrator()
        demo_nodes()
        demo_state_flow()

        print("\n" + "=" * 60)
        print("✅ 模块 3 演示全部完成!")
        print("=" * 60)

        print("\n💡 面试要点:")
        print("  1. LangGraph StateGraph 定义工作流")
        print("  2. 每个节点接收 State, 返回更新后的 State")
        print("  3. condition_handler 实现条件路由")
        print("  4. 统一错误处理节点")
        print("  5. 状态驱动的工作流推进")
        print("  6. SSE 实时推送进度到前端")

        return True

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
