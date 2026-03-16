# 面试讲解准备计划

> 目标: 将 Paper Analysis Agent 项目拆分为可独立学习讲解的技术模块
> 日期: 2026-03-13
> 状态: ✅ 已完成

---

## 项目拆分结果

已将项目拆分为 **4 个独立模块**，每个模块都有独立的演示脚本：

| 模块 | 名称 | 文件 | 状态 |
|------|------|------|------|
| 1 | 基础设施层 | `demos/demo_module_01_core.py` | ✅ 可运行 |
| 2 | 数据层 | `demos/demo_module_02_data.py` | ✅ 可运行 |
| 3 | 工作流层 | `demos/demo_module_03_orchestrator.py` | ✅ 可运行 |
| 4 | 代理层 | `demos/demo_module_04_autogen.py` | ✅ 可运行 |

---

## 使用方法

### 1. 运行所有模块

```bash
cd demos
poetry run python run_demos.py
```

### 2. 运行单个模块

```bash
# 模块 1: 基础设施层（配置、模型客户端、状态管理）
poetry run python run_demos.py 1

# 模块 2: 数据层（搜索、知识库、文档解析）
poetry run python run_demos.py 2

# 模块 3: LangGraph 工作流
poetry run python run_demos.py 3

# 模块 4: AutoGen 多代理
poetry run python run_demos.py 4
```

### 3. 查看模块列表

```bash
poetry run python run_demos.py list
```

---

## 各模块内容

### 模块 1: 基础设施层

**技术点:**
- 配置系统 (`core/config.py`): 单例模式 + Pydantic 验证 + 点表示法访问
- 模型客户端 (`core/model_client.py`): 多提供商管理 + 超时配置
- 状态管理 (`core/state_models.py`): 工作流状态定义 + SSE 通信格式

**面试要点:**
- 如何统一管理多厂商 LLM?
- 状态如何在节点间传递?
- 如何实现前端实时进度推送?

---

### 模块 2: 数据层

**技术点:**
- 论文搜索 (`tasks/paper_search.py`): arXiv API + 日期格式化
- 知识库系统 (`knowledge/`): 工厂模式 + ChromaDB + 全局元数据
- 文档解析 (`parsers/`): ParserFactory + 多格式支持

**面试要点:**
- arXiv 查询语法如何构建?
- 知识库如何支持多种类型?
- 文档解析如何扩展新格式?

---

### 模块 3: 工作流层 (LangGraph)

**技术点:**
- 编排器 (`agents/orchestrator.py`): StateGraph + 条件路由
- 节点实现 (`nodes/`): search → reading → analyse → writing → report
- 状态流转: State 驱动 + 错误处理

**工作流图:**
```
START → search_node → reading_node → analyse_node → writing_node → report_node → END
            ↓               ↓              ↓               ↓               ↓
       handle_error_node ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ← ←
```

**面试要点:**
- 如何设计工作流节点?
- 条件路由如何实现?
- 错误如何统一处理?

---

### 模块 4: 代理层 (AutoGen)

**技术点:**
- 代理类型: AssistantAgent + UserProxyAgent
- 搜索代理: 结构化输出 + 人工审核
- 分析子代理: Cluster → Deep → Global 分层分析
- 写作代理组: SelectorGroupChat + TextMentionTermination
- RAG 检索: 双知识库检索

**面试要点:**
- 如何实现人工介入?
- SelectorGroupChat 如何工作?
- RAG 如何结合私有知识?

---

## 面试讲解建议

### 推荐结构 (10-15 分钟)

1. **项目概述** (1分钟)
   - 自动化论文调研报告生成
   - 核心流程: 搜索 → 阅读 → 分析 → 写作 → 报告

2. **技术架构** (2分钟)
   - 分层设计: 基础设施 → 数据 → 工作流 → 代理
   - 技术栈: LangGraph + AutoGen + ChromaDB + arXiv

3. **核心亮点** (选 2-3 个, 8-10分钟)
   - LangGraph 工作流编排
   - AutoGen 多代理协作
   - 双源 RAG 检索

4. **总结** (1分钟)
   - 模块化设计，每个模块可独立运行
   - 人工介入机制保证可控性

---

## 参考文档

| 文件 | 说明 |
|------|------|
| `demos/README.md` | 完整使用指南和面试 Q&A |
| `findings_interview.md` | 各模块详细技术要点 |
| `demos/run_demos.py` | 演示运行主入口 |

---

## 下一步

1. 按模块顺序学习 (`poetry run python run_demos.py 1`)
2. 阅读 `findings_interview.md` 中的技术细节
3. 准备 2-3 分钟的模块讲解稿
4. 练习运行演示脚本

祝你面试顺利! 🎉
