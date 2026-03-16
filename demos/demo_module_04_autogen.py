"""
模块 4: AutoGen 多代理系统演示
可以独立运行，展示多代理协作能力
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_autogen_agents():
    """演示 AutoGen 代理类型"""
    print("=" * 60)
    print("模块 4.1: AutoGen 代理基础")
    print("=" * 60)

    print("\n🤖 AutoGen 代理类型:")
    print("""
    1. AssistantAgent
       - 执行任务, 调用 LLM
       - 支持结构化输出 (output_content_type)
       - 示例: 搜索代理、分析代理

    2. UserProxyAgent
       - 代表用户介入
       - 可暂停等待人工输入
       - 示例: WebUserProxyAgent

    3. SelectorGroupChat
       - 多代理群组对话
       - LLM 动态选择下一个发言者
       - 适用于复杂协作任务
    """)

    print("\n📋 项目中使用的代理:")
    agents = {
        "search_agent": "AssistantAgent - 提取搜索关键词",
        "userProxyAgent": "UserProxyAgent - 人工审核",
        "cluster_agent": "AssistantAgent - 论文聚类",
        "deep_analyse_agent": "AssistantAgent - 深度分析",
        "global_analyse_agent": "AssistantAgent - 综合分析",
        "writing_director": "AssistantAgent - 大纲生成",
        "writing_agent": "AssistantAgent - 章节写作",
        "retrieval_agent": "AssistantAgent - RAG检索",
        "review_agent": "AssistantAgent - 质量审核",
    }
    for name, desc in agents.items():
        print(f"  - {name}: {desc}")

    print("\n✅ 代理类型演示完成")
    return True


def demo_search_agent():
    """演示搜索代理"""
    print("\n" + "=" * 60)
    print("模块 4.2: 搜索代理 + UserProxy")
    print("=" * 60)

    print("\n🔍 搜索代理设计:")
    print("""
    核心功能: 提取搜索关键词 + 人工审核

    代码结构:
      class SearchQuery(BaseModel):
          querys: List[str]          # 英文关键词列表
          start_date: Optional[str]  # 开始日期
          end_date: Optional[str]    # 结束日期

      search_agent = AssistantAgent(
          name="search_agent",
          model_client=model_client,
          system_message=search_agent_prompt,
          output_content_type=SearchQuery,  # 关键: 结构化输出
      )

    人工介入流程:
      1. LLM 生成 SearchQuery
      2. 推送到前端等待审核
      3. UserProxyAgent 挂起等待输入
      4. 用户修改后返回
      5. 使用审核后的关键词搜索
    """)

    print("\n📝 UserProxyAgent 实现要点:")
    print("""
    class WebUserProxyAgent(UserProxyAgent):
        def __init__(self):
            self.future = None  # asyncio.Future

        async def on_messages(self, messages, ...):
            # 创建 Future 并挂起
            self.future = asyncio.Future()
            # 等待前端 POST /send_input
            return await self.future

        def submit_user_input(self, user_input):
            # 前端调用此方法提交用户输入
            if self.future and not self.future.done():
                self.future.set_result(user_input)
    """)

    print("\n✅ 搜索代理演示完成")
    return True


def demo_analysis_agents():
    """演示分析子代理"""
    print("\n" + "=" * 60)
    print("模块 4.3: 分析子代理 (sub_analyse_agent/)")
    print("=" * 60)

    print("\n📊 分析流程:")
    print("""
    输入: ExtractedPapersData (多篇论文的结构化数据)
      ↓
    [Cluster Agent] - KMeans + LLM 主题聚类
      - 将论文分为若干主题簇
      - 使用 LLM 为每个簇命名
      ↓
    [Deep Analyse Agent] - 每簇深度分析
      - 分析每个主题簇的共同特点
      - 提取关键方法和创新点
      ↓
    [Global Analyse Agent] - 跨簇综合分析
      - 对比不同主题簇
      - 识别研究趋势和空白
      ↓
    输出: 分析报告 (JSON 格式)
    """)

    print("\n🎯 Cluster Agent 核心逻辑:")
    print("""
    def cluster_papers(papers, n_clusters=3):
        # 1. Embedding 向量化
        embeddings = embedding_model.encode([p.summary for p in papers])

        # 2. KMeans 聚类
        kmeans = KMeans(n_clusters=n_clusters)
        labels = kmeans.fit_predict(embeddings)

        # 3. LLM 主题命名
        for cluster_id in range(n_clusters):
            cluster_papers = [p for i, p in enumerate(papers) if labels[i] == cluster_id]
            topic_name = llm.generate_topic_name(cluster_papers)

        return clusters
    """)

    print("\n✅ 分析代理演示完成")
    return True


def demo_writing_group():
    """演示写作代理组"""
    print("\n" + "=" * 60)
    print("模块 4.4: 写作代理组 (SelectorGroupChat)")
    print("=" * 60)

    print("\n✍️  写作代理组设计:")
    print("""
    成员:
      1. Writing Director (写作主管)
         - 首先执行
         - 生成报告大纲

      2. Writing Agent (写作代理)
         - 根据大纲撰写章节
         - 调用 Retrieval Agent 获取资料

      3. Retrieval Agent (检索代理)
         - RAG 检索知识库
         - 为写作提供参考资料

      4. Review Agent (审核代理)
         - 审核章节质量
         - 通过则输出 "APPROVE"

    协作模式:
      SelectorGroupChat - LLM 根据对话选择下一个发言者
    """)

    print("\n📝 SelectorGroupChat 实现:")
    print("""
    from autogen_agentchat.teams import SelectorGroupChat
    from autogen_agentchat.conditions import TextMentionTermination

    def create_writing_group(state_queue=None):
        model_client = create_default_client()

        # 终止条件: 出现 "APPROVE"
        text_termination = TextMentionTermination("APPROVE")

        # 创建代理
        writing_agent = create_writing_agent(state_queue)
        review_agent = create_review_agent(state_queue)
        retrieval_agent = create_retrieval_agent(state_queue)

        # 创建选择器群组
        task_group = SelectorGroupChat(
            [writing_agent, retrieval_agent, review_agent],
            model_client=model_client,
            termination_condition=text_termination,
            selector_prompt=selector_prompt,
            allow_repeated_speaker=False,
        )
        return task_group

    # 运行
    result = await task_group.run(task=writing_task)
    """)

    print("\n🔄 典型对话流程:")
    print("""
    Director:   生成大纲: 1.引言 2.方法 3.结果 4.讨论
    Writing:    开始撰写引言章节...
    Retrieval:  检索相关资料...
    Writing:    引言完成，开始撰写方法章节...
    Retrieval:  检索方法相关资料...
    Writing:    方法章节完成...
    ...
    Review:     审核通过。APPROVE
    [终止]
    """)

    print("\n✅ 写作代理组演示完成")
    return True


def demo_retrieval_agent():
    """演示 RAG 检索代理"""
    print("\n" + "=" * 60)
    print("模块 4.5: RAG 检索代理")
    print("=" * 60)

    print("\n🔍 RAG 检索代理功能:")
    print("""
    职责:
      1. 接收 Writing Agent 的查询请求
      2. 从知识库检索相关文档
      3. 整理结果返回给 Writing Agent

    双知识库检索:
      - 临时知识库 (tmp_db): arXiv 论文
      - 用户知识库 (user_db): 上传的私有文档
    """)

    print("\n📋 检索代理实现:")
    print("""
    async def retrieval_agent_run(task: str) -> str:
        # 1. 生成查询向量
        queries = extract_queries(task)

        # 2. 从临时知识库检索
        tmp_results = await knowledge_base.aquery(
            queries, db_id=tmp_db_id, top_k=5
        )

        # 3. 从用户知识库检索
        user_results = await knowledge_base.aquery(
            queries, db_id=user_db_id, top_k=5
        )

        # 4. 合并并格式化结果
        all_results = tmp_results + user_results
        return format_results(all_results)
    """)

    print("\n✅ RAG 检索代理演示完成")
    return True


async def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("模块 4: AutoGen 多代理系统演示")
    print("=" * 60)
    print("\n包含:")
    print("  - AutoGen 代理类型")
    print("  - 搜索代理 + UserProxy")
    print("  - 分析子代理")
    print("  - 写作代理组")
    print("  - RAG 检索代理")

    try:
        demo_autogen_agents()
        demo_search_agent()
        demo_analysis_agents()
        demo_writing_group()
        demo_retrieval_agent()

        print("\n" + "=" * 60)
        print("✅ 模块 4 演示全部完成!")
        print("=" * 60)

        print("\n💡 面试要点:")
        print("  1. AssistantAgent 执行任务, UserProxyAgent 人工介入")
        print("  2. 结构化输出约束 LLM 返回格式")
        print("  3. SelectorGroupChat 实现多代理协作")
        print("  4. TextMentionTermination 控制对话终止")
        print("  5. 分层分析: 聚类 → 深度分析 → 综合分析")
        print("  6. RAG 结合外部论文和私有知识库")

        return True

    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
