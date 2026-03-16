# 面试讲解技术要点

> 各模块核心技术细节和面试重点

---

## 模块 1: 模型客户端 (Model Client)

### 核心设计
```python
# 工厂模式 + 配置驱动
@dataclass
class TimeoutConfig:
    connect: float = 60.0
    read: float = 300.0
    total: float = 600.0

class ModelClient:
    FAMILY_MAP = {
        'siliconflow': 'Qwen',
        'openai': 'GPT',
        'dashscope': 'Qwen',
        'ark': 'Qwen',
    }
```

### 面试要点
1. **多提供商支持**: 通过配置统一管理不同厂商的模型
2. **超时策略**: 不同任务类型有不同的超时配置
3. **模型能力声明**: 通过 ModelInfo 声明模型能力

### 可能的面试官问题
- Q: 如何切换不同的模型提供商?
- A: 通过配置文件指定 provider, model, api_key, base_url

---

## 模块 2: 论文搜索 (Paper Search)

### 核心流程
```
用户查询 → LLM提取关键词 → 日期格式化 → arXiv API → 结果解析
```

### 关键代码
```python
# arXiv 查询构建
search_query = ""
for query in querys:
    search_query += "all:%22"+query+"%22 OR "
search_query = search_query[:-4]

# 日期过滤
date_filter = f"submittedDate:[{start_date_str} TO {end_date_str}]"
search_query = f"({search_query}) AND {date_filter}"
```

### 面试要点
1. **arXiv 查询语法**: 使用 `all:` 和 `%22` (URL编码的引号)
2. **日期处理**: 支持多种日期格式,统一转为 YYYYMMDD0000
3. **容错设计**: 带重试机制的搜索

---

## 模块 3: 知识库系统 (Knowledge Base)

### 架构设计
```
KnowledgeBaseManager (统一入口)
    ├── global_metadata.json (全局元数据)
    ├── kb_instances: {kb_type: KnowledgeBase}
    └── _get_kb_for_database(db_id) → KnowledgeBase
```

### 核心能力
| 能力 | 方法 | 说明 |
|------|------|------|
| CRUD | create_database/delete_database | 数据库管理 |
| 索引 | add_content | 文档向量化入库 |
| 检索 | aquery | 异步向量查询 |
| 元数据 | get_file_info | 文件信息管理 |

### 面试要点
1. **工厂模式**: `KnowledgeBaseFactory.create(kb_type)`
2. **元数据管理**: 全局 JSON 文件统一管理所有知识库
3. **异步设计**: 所有 IO 操作都是异步的

---

## 模块 4: LangGraph 工作流编排

### 状态图定义
```python
builder = StateGraph(State, context_schema=ConfigSchema)
builder.add_node("search_node", search_node)
builder.add_node("reading_node", reading_node)
# ...
builder.add_conditional_edges("search_node", condition_handler)
```

### 条件路由
```python
def condition_handler(self, state: State) -> str:
    if current_step == ExecutionState.SEARCHING:
        if err.search_node_error:
            return "handle_error_node"
        return "reading_node"
    # ...
```

### 面试要点
1. **状态驱动**: 每个节点接收和返回 State
2. **条件边**: 根据状态决定下一步走向
3. **错误处理**: 统一错误节点处理异常

---

## 模块 5: AutoGen 多代理系统

### 搜索代理示例
```python
search_agent = AssistantAgent(
    name="search_agent",
    model_client=model_client,
    system_message=search_agent_prompt,
    output_content_type=SearchQuery,  # 结构化输出
)
```

### 写作代理组 (SelectorGroupChat)
```python
task_group = SelectorGroupChat(
    [writing_agent, retrieval_agent, review_agent],
    model_client=model_client,
    termination_condition=TextMentionTermination("APPROVE"),
    selector_prompt=selector_prompt,
    allow_repeated_speaker=False,
)
```

### 面试要点
1. **代理类型**: AssistantAgent (执行任务) vs UserProxyAgent (人工介入)
2. **结构化输出**: 通过 Pydantic 模型约束 LLM 输出
3. **选择器群组**: LLM 动态选择下一个发言代理
4. **终止条件**: 特定文本触发结束

### 可能的面试官问题
- Q: 写作代理组是如何协作的?
- A: 使用 SelectorGroupChat, LLM 根据对话内容选择下一个发言者, 由 review_agent 审核通过后输出 APPROVE 终止

---

## 模块 6: RAG 检索

### 双知识库检索
```python
async def retrieval_tool(querys: List[str]):
    # 1. 从临时知识库检索 (arXiv 论文)
    tmpdb_results = await knowledge_base.aquery(
        querys, db_id=tmp_db_id, top_k=config.get_int("tmpdb_top_k")
    )

    # 2. 从用户知识库检索 (上传文档)
    db_results = await knowledge_base.aquery(
        querys, db_id=current_db_id, top_k=config.get_int("top_k")
    )
```

### 面试要点
1. **双源检索**: 结合外部论文和用户私有知识
2. **阈值控制**: 相似度阈值过滤低质量结果
3. **上下文增强**: 检索结果 + 来源信息

---

## 整体项目亮点总结

### 技术亮点
1. **多框架融合**: LangGraph (工作流) + AutoGen (多代理) 结合使用
2. **模块化设计**: 每个功能模块可独立运行和测试
3. **配置驱动**: 模型、参数都通过 YAML/JSON 配置
4. **异步全链路**: 从 API 到数据库全异步实现

### 设计亮点
1. **人工介入**: UserProxyAgent 在关键节点暂停等待审核
2. **错误处理**: 统一错误节点, 不中断整体工作流
3. **可观测性**: SSE 实时推送进度到前端

### 面试结束语
"这个项目最核心的设计是**分层架构**:
- 底层是模型和存储基础设施
- 中间层是搜索/知识库/RAG等能力模块
- 上层用 LangGraph 编排工作流, AutoGen 实现多代理协作
这样的架构让每个模块都可以独立演进和测试。"
