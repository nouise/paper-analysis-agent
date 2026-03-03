# Paper Analysis Agent —— AI 驱动的学术调研报告生成系统

Paper Analysis Agent 是一个基于多智能体协作的学术论文调研系统。用户只需输入一个研究主题，系统即可自动完成**论文检索 → 论文阅读 → 聚类分析 → 分章写作 → 报告生成**的全流程，并输出一份结构完整的 Markdown 调研报告。

整个过程通过 **SSE（Server-Sent Events）** 实时推送进度到浏览器，并在关键步骤（搜索关键词）引入**人工审核**，让用户对检索策略进行把关。

![LangGraph Workflow](https://img.shields.io/badge/Workflow-LangGraph-blue)
![AutoGen Agents](https://img.shields.io/badge/Agents-AutoGen-green)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Vue3](https://img.shields.io/badge/Frontend-Vue3-4FC08D)

---

## 目录

- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [工作流程](#工作流程)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [API 接口](#api-接口)
- [License](#license)

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **多智能体协作** | 基于 AutoGen 构建搜索、阅读、分析、写作、报告五大智能体，各司其职 |
| **LangGraph 工作流** | 使用 LangGraph StateGraph 编排节点，支持条件分支和错误重试 |
| **人工审核** | 在搜索阶段暂停工作流，等待用户确认/修改检索关键词后再继续 |
| **SSE 实时推送** | 前端通过 EventSource 接收每个节点的实时状态（初始化 / 思考中 / 生成中 / 完成） |
| **并行处理** | 论文阅读和分章写作均使用 `asyncio.gather` 并发执行，大幅缩短总耗时 |
| **RAG 检索增强** | 论文数据自动存入 ChromaDB，写作阶段可检索相关内容辅助撰写 |
| **知识库管理** | 支持创建、上传、查询自定义知识库，写作时可引入用户私有资料 |
| **报告管理** | 自动保存为 Markdown 文件，支持在线浏览、编辑、删除历史报告 |
| **微信公众号集成** | 一键将报告转换为微信公众号格式并发布到草稿箱（新功能 🆕） |

---

## 🆕 微信公众号功能

Paper Analysis Agent 现已支持将生成的研究报告一键转换为微信公众号格式：

### 功能特性

- ✅ **Markdown → HTML 转换**：自动转换为适合微信的美化 HTML
- ✅ **三种主题风格**：科技风（蓝紫渐变）、简约风（黑白灰）、商务风（深蓝金色）
- ✅ **前端预览**：在浏览器中预览转换效果
- ✅ **一键发布**：直接发布到微信公众号草稿箱
- ✅ **自动上传图片**：自动处理图片上传到微信 CDN

### 快速使用

1. 在历史报告页面点击任意报告的"查看详情"
2. 点击右上角 **📱 微信公众号** 按钮
3. 选择主题风格（科技风/简约风/商务风）
4. 点击 **🔄 转换为 HTML** 预览效果
5. 点击 **🚀 一键发布到微信** 发布到草稿箱

### 配置说明

详细配置和使用说明请查看 [WECHAT_SETUP.md](WECHAT_SETUP.md)

**快速测试**：
```bash
python test_wechat.py
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Vue 3 Frontend                       │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 查询输入  │  │ SSE 进度展示  │  │ 报告展示 / 编辑  │  │
│  └────┬─────┘  └──────▲───────┘  └──────────────────┘  │
│       │               │                                 │
│       │  EventSource  │  /send_input (人工审核)          │
└───────┼───────────────┼─────────────────────────────────┘
        │  GET /api/    │  POST
        │  research     │
┌───────▼───────────────┼─────────────────────────────────┐
│                  FastAPI Backend                         │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │           LangGraph StateGraph                  │   │
│   │                                                 │   │
│   │  search ──► reading ──► analyse ──► writing     │   │
│   │    │                                    │       │   │
│   │    │ (人工审核)                          ▼       │   │
│   │    └─ userProxyAgent              report ──► END│   │
│   │         (Future 等待)                           │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
│   asyncio.Queue ──► SSE EventSourceResponse             │
│   ChromaDB (向量存储)    arXiv API (论文检索)             │
└─────────────────────────────────────────────────────────┘
```

---

## 工作流程

### 1. Search（论文搜索 + 人工审核）

LLM 将用户的自然语言需求转换为结构化查询条件（关键词列表、时间范围），通过 SSE 推送至前端供用户审核。前端修改确认后，调用 arXiv API 检索论文。

> **人工审核机制**：`WebUserProxyAgent` 内部创建 `asyncio.Future`，`await` 等待前端 POST `/send_input` 提交审核结果后自动唤醒工作流。

### 2. Reading（论文阅读）

使用 `asyncio.gather` 并行阅读所有检索到的论文，LLM 提取每篇论文的核心问题、关键方法、数据集、评估指标、主要结果、局限性等结构化信息，并存入 ChromaDB 向量数据库。

### 3. Analyse（聚类 + 深度分析 + 全局分析）

三阶段分析流程：
- **聚类**：基于嵌入向量 + KMeans 将论文按主题分组，LLM 生成主题描述
- **深度分析**：并行分析每个聚类的技术路线、方法对比、应用领域
- **全局分析**：汇总各聚类结果，生成涵盖技术趋势、研究热点、局限性、未来展望的综合分析

### 4. Writing（分章并行写作）

- **写作主管**根据全局分析生成报告大纲，拆分为多个写作子任务
- 每个子任务由 **writing_agent + retrieval_agent + review_agent** 三智能体协作完成
  - `writing_agent`：撰写章节内容
  - `retrieval_agent`：从 ChromaDB 检索补充资料（来源包括 arXiv 论文和用户知识库）
  - `review_agent`：审查质量，通过后输出 `APPROVE` 终止该子任务
- 所有子任务并发执行

### 5. Report（报告生成）

汇总所有章节，LLM 补充过渡语句组装成完整报告，流式输出到前端，同时保存为 `output/reports/report_<timestamp>_<query>.md`。

---

## 项目结构

```
Paper-Agent/
├── main.py                          # FastAPI 入口（SSE、人工审核、报告 API）
├── pyproject.toml                   # Poetry 依赖管理
├── example.env                      # 环境变量模板
├── design.md                        # 详细设计文档
│
├── src/
│   ├── agents/                      # 智能体定义
│   │   ├── orchestrator.py          # LangGraph 工作流编排（核心）
│   │   ├── search_agent.py          # 搜索智能体
│   │   ├── reading_agent.py         # 阅读智能体
│   │   ├── analyse_agent.py         # 分析智能体
│   │   ├── writing_agent.py         # 写作智能体
│   │   ├── report_agent.py          # 报告生成智能体
│   │   ├── userproxy_agent.py       # 人工审核代理（Future 机制）
│   │   ├── sub_analyse_agent/       # 分析子智能体（聚类 / 深度分析 / 全局分析）
│   │   └── sub_writing_agent/       # 写作子智能体（主管 / 写作 / 检索 / 审查）
│   │
│   ├── nodes/                       # LangGraph 节点函数
│   │   ├── search.py                # 搜索节点（含人工审核逻辑）
│   │   ├── reading.py               # 阅读节点
│   │   ├── analyse.py               # 分析节点
│   │   ├── writing.py               # 写作节点
│   │   └── report.py                # 报告节点
│   │
│   ├── core/                        # 核心配置
│   │   ├── config.py                # 配置加载
│   │   ├── model_client.py          # LLM 客户端封装
│   │   ├── models.yaml              # 模型配置（模型选择 / API 端点）
│   │   ├── prompts.py               # Prompt 模板
│   │   ├── state_models.py          # 状态数据模型
│   │   └── system_params.yaml       # 系统参数
│   │
│   ├── knowledge/                   # 知识库模块
│   │   ├── knowledge_router.py      # 知识库 REST API
│   │   └── knowledge/               # ChromaDB 封装（CRUD、索引、检索）
│   │
│   ├── services/                    # 业务服务
│   │   ├── report_service.py        # 报告文件 CRUD
│   │   ├── chroma_client.py         # ChromaDB 客户端
│   │   └── retrieval_tool.py        # 检索工具
│   │
│   ├── tasks/
│   │   └── paper_search.py          # arXiv 论文检索
│   │
│   ├── plugins/                     # 插件（OCR 等）
│   └── utils/                       # 工具函数（日志、时间、工具调用）
│
├── web/                             # Vue 3 前端
│   ├── src/
│   │   ├── App.vue                  # 主页面（查询、SSE 进度、报告展示/编辑）
│   │   ├── views/
│   │   │   ├── History.vue          # 历史报告管理
│   │   │   └── KnowledgeBase.vue    # 知识库管理
│   │   ├── components/              # 通用组件
│   │   └── router/                  # Vue Router
│   ├── vite.config.js               # Vite 配置（API 代理）
│   └── package.json
│
├── data/knowledge_base_data/        # 知识库运行时数据
└── output/
    ├── reports/                     # 生成的报告（.md）
    └── log/                         # 运行日志
```

---

## 快速开始

### 环境要求

- Python 3.12
- Node.js 18+
- [Poetry](https://python-poetry.org/)

### 1. 安装后端依赖

```bash
cd Paper-Agent
cp example.env .env
# 编辑 .env，填入你的 API Key（至少需要 DASHSCOPE_API_KEY）

poetry install
```

### 2. 安装前端依赖

```bash
cd web
npm install
```

### 3. 启动服务

**启动后端**（默认端口 8000）：

```bash
poetry run uvicorn main:app --host 0.0.0.0 --port 8000
```

**启动前端**（默认端口 5173）：

```bash
cd web
npm run dev
```

浏览器访问 `http://localhost:5173`，输入研究主题即可开始调研。

---

## 配置说明

### 环境变量（`.env`）

```dotenv
DASHSCOPE_API_KEY=your_dashscope_api_key    # 必填：阿里云 DashScope
SILICONFLOW_API_KEY=sk-xxx                  # 可选：SiliconFlow
OPENAI_API_KEY=sk-xxx                       # 可选：OpenAI
ARK_API_KEY=xxx                             # 可选：火山引擎
```

### 模型配置（`src/core/models.yaml`）

每个节点可独立配置使用的模型和提供商，默认全部使用 DashScope 的 `qwen3.5-plus`：

```yaml
default-model:
  model-provider: dashscope
  model: qwen3.5-plus
  enable_thinking: false

default-embedding-model:
  model-provider: dashscope
  model: text-embedding-v4
  dimension: 1024
```

支持的模型提供商：`dashscope`、`siliconflow`、`openai`、`ark`。

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/research?query=...` | 启动调研，返回 SSE 事件流 |
| `POST` | `/send_input` | 提交人工审核结果 `{"input": "..."}` |
| `GET` | `/api/reports` | 获取所有历史报告列表 |
| `GET` | `/api/reports/{filename}` | 获取单个报告详情 |
| `PUT` | `/api/reports/{filename}` | 更新报告内容 `{"content": "..."}` |
| `DELETE` | `/api/reports/{filename}` | 删除报告 |
| `GET/POST` | `/knowledge/...` | 知识库管理（创建、上传、查询、删除） |

### SSE 事件数据格式

```json
{
  "step": "searching | reading | analysing | writing | reporting",
  "state": "initializing | thinking | generating | user_review | completed | error | finished",
  "data": "..."
}
```

---

## License

[MIT](LICENSE)
