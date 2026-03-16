# Paper Analysis Agent - 面试讲解指南

> 本项目已将各个技术模块拆分为独立的演示脚本，方便面试时逐一讲解。

---

## 快速开始

### 运行所有模块演示

```bash
cd demos
python run_demos.py
```

### 运行指定模块

```bash
# 模块 1: 基础设施层
python run_demos.py 1

# 模块 2: 数据层
python run_demos.py 2

# 模块 3: LangGraph 工作流
python run_demos.py 3

# 模块 4: AutoGen 多代理
python run_demos.py 4
```

### 查看模块列表

```bash
python run_demos.py list
```

---

## 模块结构

### 模块 1: 基础设施层 (`demo_module_01_core.py`)

**包含内容:**
- 配置系统 (`core/config.py`)
- 模型客户端 (`core/model_client.py`)
- 状态管理 (`core/state_models.py`)

**面试要点:**
1. 配置系统使用单例模式 + Pydantic 验证
2. 支持点表示法访问嵌套配置 (如 `config.get('default-model.model')`)
3. 模型客户端统一管理多提供商 LLM (siliconflow/dashscope/openai/ark)
4. 预定义超时配置策略 (default/quick/long/embedding)
5. 状态模型定义工作流数据结构 (PaperAgentState, BackToFrontData)

---

### 模块 2: 数据层 (`demo_module_02_data.py`)

**包含内容:**
- 论文搜索 (`tasks/paper_search.py`)
- 知识库系统 (`knowledge/`)
- 文档解析 (`parsers/`)

**面试要点:**
1. 论文搜索使用 arXiv API，支持多种日期格式
2. arXiv 查询语法构建 (`all:%22keyword%22`)
3. 知识库使用工厂模式管理多种类型 (ChromaDB)
4. 全局元数据统一管理所有知识库
5. 文档解析支持 PDF/DOCX/MD/TXT，统一接口

---

### 模块 3: 工作流层 (`demo_module_03_orchestrator.py`)

**包含内容:**
- 编排器 (`agents/orchestrator.py`)
- 工作流节点 (`nodes/`)

**工作流图:**
```
START → search_node → reading_node → analyse_node → writing_node → report_node → END
            ↓               ↓              ↓               ↓               ↓
       handle_error_node ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

**面试要点:**
1. LangGraph StateGraph 定义工作流
2. 每个节点接收 State，返回更新后的 State
3. `condition_handler` 实现条件路由 (正常流程 vs 错误处理)
4. 统一错误处理节点
5. SSE 实时推送进度到前端

---

### 模块 4: 代理层 (`demo_module_04_autogen.py`)

**包含内容:**
- AutoGen 代理类型
- 搜索代理 + UserProxy
- 分析子代理
- 写作代理组 (SelectorGroupChat)
- RAG 检索代理

**面试要点:**
1. **AssistantAgent**: 执行任务，支持结构化输出
2. **UserProxyAgent**: 人工介入，使用 `asyncio.Future` 暂停等待
3. **SelectorGroupChat**: LLM 动态选择下一个发言代理
4. **TextMentionTermination**: 特定文本触发终止
5. 分层分析: 聚类 → 深度分析 → 综合分析
6. RAG 结合临时知识库 (arXiv) 和用户知识库

---

## 面试讲解建议

### 推荐讲解结构 (10-15 分钟)

#### 1. 项目概述 (1分钟)

```
这是一个自动化论文调研报告生成系统。
核心流程: 搜索论文 → 阅读分析 → 聚类整理 → 协作写作 → 生成报告
技术栈: LangGraph (工作流) + AutoGen (多代理) + ChromaDB (知识库) + arXiv API
```

#### 2. 技术架构 (2分钟)

```
分层架构:
- 基础设施层: 配置管理、模型客户端、状态管理
- 数据层: 论文搜索、知识库、文档解析
- 工作流层: LangGraph 编排 5 个节点
- 代理层: AutoGen 实现多代理协作
```

#### 3. 核心亮点 (选 2-3 个重点，8-10分钟)

**推荐重点 1: LangGraph 工作流编排**
```
使用 StateGraph 定义工作流:
- 5 个节点串联: search → reading → analyse → writing → report
- 条件路由: 每个节点后检查错误状态
- 状态驱动: 所有数据通过 PaperAgentState 传递
```

**推荐重点 2: AutoGen 多代理协作**
```
写作代理组使用 SelectorGroupChat:
- Writing Agent: 撰写章节
- Retrieval Agent: RAG 检索
- Review Agent: 审核并输出 APPROVE 终止
- LLM 根据对话内容动态选择下一个发言者
```

**推荐重点 3: 双源 RAG 检索**
```
检索工具同时查询两个知识库:
- 临时知识库: 存储搜索到的 arXiv 论文
- 用户知识库: 存储用户上传的私有文档
- 结合外部公开资料和用户私有知识
```

#### 4. 总结 (1分钟)

```
这个项目最核心的设计是分层架构和模块化:
- 每个模块都可以独立运行和测试
- LangGraph 和 AutoGen 结合使用，各取所长
- 人工介入机制保证关键节点可控
```

---

## 可能的面试官问题

### Q1: 如何支持不同的 LLM 提供商?

A: 通过配置系统和模型客户端实现:
```python
# models.yaml
default-model:
  model-provider: siliconflow
  model: Qwen/Qwen3-32B

siliconflow:
  base_url: https://api.siliconflow.cn/v1
  api_key: ${SILICONFLOW_API_KEY}
```

### Q2: 工作流中的错误如何处理?

A: 统一错误处理节点:
```python
def condition_handler(self, state: State) -> str:
    if state.error.search_node_error:
        return "handle_error_node"
    return "next_node"
```

### Q3: 如何实现人工审核?

A: UserProxyAgent + asyncio.Future:
```python
class WebUserProxyAgent:
    async def on_messages(self, messages, ...):
        self.future = asyncio.Future()
        return await self.future  # 挂起等待

    def submit_user_input(self, user_input):
        self.future.set_result(user_input)  # 前端调用
```

### Q4: 写作代理如何协作?

A: SelectorGroupChat 动态选择:
```python
task_group = SelectorGroupChat(
    [writing_agent, retrieval_agent, review_agent],
    model_client=model_client,
    termination_condition=TextMentionTermination("APPROVE"),
)
```

### Q5: RAG 如何结合用户私有知识?

A: 双知识库检索:
```python
# 从临时知识库检索 (arXiv 论文)
tmp_results = await knowledge_base.aquery(queries, db_id=tmp_db_id)

# 从用户知识库检索 (私有文档)
user_results = await knowledge_base.aquery(queries, db_id=user_db_id)
```

---

## 文件索引

| 文件 | 说明 |
|------|------|
| `task_plan_interview.md` | 学习计划 |
| `findings_interview.md` | 技术要点 |
| `demos/run_demos.py` | 演示运行器 |
| `demos/demo_module_01_core.py` | 基础设施演示 |
| `demos/demo_module_02_data.py` | 数据层演示 |
| `demos/demo_module_03_orchestrator.py` | LangGraph 演示 |
| `demos/demo_module_04_autogen.py` | AutoGen 演示 |

---

## 环境要求

- Python 3.9+
- 安装项目依赖: `poetry install` 或 `pip install -r requirements.txt`
- 配置环境变量: `cp example.env .env` 并设置 API 密钥

---

祝你面试顺利! 🎉
