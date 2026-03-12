# Paper Analysis Agent - 实施状态与优化方案

**文档日期**: 2026-03-11

---

## 1. 当前实施状态总览

### 1.1 已完成功能 ✅

| 模块 | 功能 | 状态 | 代码位置 |
|------|------|------|----------|
| **核心工作流** | SSE 实时推送 | ✅ 完成 | `main.py`, `src/agents/orchestrator.py` |
| | 论文搜索 (arXiv) | ✅ 完成 | `src/nodes/search.py` |
| | 用户审核机制 | ✅ 完成 | `src/agents/userproxy_agent.py` |
| | 论文并行阅读 | ✅ 完成 | `src/nodes/reading.py` |
| | 聚类分析 | ✅ 完成 | `src/agents/sub_analyse_agent/cluster_agent.py` |
| | 深度分析 | ✅ 完成 | `src/agents/sub_analyse_agent/deep_analyse_agent.py` |
| | 全局分析 | ✅ 完成 | `src/agents/sub_analyse_agent/global_analyse_agent.py` |
| | 并行写作 | ✅ 完成 | `src/nodes/writing.py`, `sub_writing_agent/` |
| | 报告生成 | ✅ 完成 | `src/nodes/report.py` |
| **知识库** | 创建/删除知识库 | ✅ 完成 | `src/knowledge/knowledge_router.py` |
| | 文件上传 | ✅ 完成 | `knowledge_router.py:upload_file` |
| | 基础查询 | ✅ 完成 | `src/knowledge/knowledge/manager.py` |
| | ChromaDB 集成 | ✅ 完成 | `src/knowledge/knowledge/implementations/chroma.py` |
| **报告管理** | 历史报告列表 | ✅ 完成 | `src/services/report_service.py` |
| | 报告查看/编辑/删除 | ✅ 完成 | `main.py:api/reports/*` |
| **微信集成** | Markdown 转 HTML | ✅ 完成 | `wechat_article_skills/` |
| | 主题风格切换 | ✅ 完成 | 科技/简约/商务风 |
| | 发布到草稿箱 | ✅ 完成 | `src/services/wechat_service.py` |

### 1.2 待开发功能 🔨

| 模块 | 功能 | 优先级 | 预计工期 | 技术难点 |
|------|------|--------|----------|----------|
| **搜索配置** | 可配置论文数量 | P0 | 2 天 | 需要前后端配合修改 |
| **前端展示** | 环节可折叠/展开 | P0 | 3 天 | 需要重新设计状态管理 |
| | 流式输出实时显示 | P1 | 3 天 | SSE 数据结构调整 |
| **知识库增强** | 随机命名生成 | P0 | 1 天 | 简单 |
| | PDF 文档解析 | P0 | 3 天 | 需要引入解析库 |
| | Word 文档解析 | P0 | 2 天 | python-docx 集成 |
| | 文档预览/管理 | P1 | 3 天 | UI 设计 |
| **生产就绪** | 数据库存储 | P1 | 4 天 | SQLite/PostgreSQL |
| | 任务历史/重试 | P1 | 3 天 | 状态机设计 |
| | 错误恢复机制 | P1 | 3 天 | 异常处理增强 |
| | 用户配置持久化 | P1 | 2 天 | LocalStorage/DB |
| | 限流/并发控制 | P2 | 3 天 | 队列机制 |

---

## 2. 详细代码架构分析

### 2.1 后端架构

```
src/
├── agents/                    # 智能体层
│   ├── orchestrator.py       # LangGraph 工作流编排（核心）
│   ├── search_agent.py       # 搜索智能体（已迁移到 nodes）
│   ├── reading_agent.py      # 阅读智能体
│   ├── analyse_agent.py      # 分析智能体（聚类+深度+全局）
│   ├── writing_agent.py      # 写作智能体
│   ├── report_agent.py       # 报告生成智能体
│   ├── userproxy_agent.py    # 用户审核代理（Future 机制）
│   └── sub_*/                # 子智能体目录
│
├── nodes/                     # LangGraph 节点实现
│   ├── search.py             # 搜索节点（默认 max_results=5）⚠️
│   ├── reading.py            # 阅读节点
│   ├── analyse.py            # 分析节点
│   ├── writing.py            # 写作节点
│   └── report.py             # 报告节点
│
├── core/                      # 核心配置
│   ├── config.py             # 配置加载
│   ├── model_client.py       # LLM 客户端封装
│   ├── models.yaml           # 模型配置
│   ├── prompts.py            # Prompt 模板
│   ├── state_models.py       # 状态数据模型
│   └── system_params.yaml    # 系统参数
│
├── knowledge/                 # 知识库模块
│   ├── knowledge_router.py   # REST API（缺少解析功能）⚠️
│   └── knowledge/            # ChromaDB 封装
│       ├── base.py
│       ├── factory.py
│       ├── manager.py
│       ├── indexing.py       # 文档索引（需要增强）⚠️
│       └── implementations/
│
├── services/                  # 业务服务
│   ├── report_service.py     # 报告管理
│   ├── chroma_client.py      # ChromaDB 客户端
│   ├── retrieval_tool.py     # 检索工具
│   └── wechat_service.py     # 微信服务
│
├── tasks/                     # 任务模块
│   └── paper_search.py       # arXiv 搜索（默认 5 篇）⚠️
│
└── plugins/                   # 插件（已预留 OCR）
    ├── guard.py
    ├── paddlex.py
    └── _ocr.py
```

### 2.2 前端架构

```
web/src/
├── api/
│   ├── knowledge.js          # 知识库 API
│   └── report.js             # 报告 API（待创建）⚠️
├── components/
│   ├── CreateDatabaseModal.vue   # 创建知识库（缺少随机命名）⚠️
│   ├── DatabaseCard.vue
│   ├── FileUpload.vue        # 文件上传（缺少解析状态显示）⚠️
│   ├── QueryTest.vue
│   ├── SelectKnowledgeModal.vue
│   ├── MainContent.vue       # 主内容（缺少折叠面板）⚠️
│   ├── ProgressPanel.vue     # 进度面板（待创建）⚠️
│   └── StepCard.vue          # 环节卡片（待创建）⚠️
├── views/
│   ├── HomeView.vue          # 主页（缺少数量设置）⚠️
│   ├── History.vue           # 历史报告
│   └── KnowledgeBase.vue     # 知识库管理
├── router/
│   └── index.js
└── stores/                   # Pinia Store（待创建）⚠️
    └── workflow.js           # 工作流状态管理
```

---

## 3. 核心修改方案

### 3.1 搜索论文数量可配置

**当前代码** (`src/nodes/search.py:173`):
```python
results = await searcher.search_papers(
    querys=search_query.querys,
    max_results=current_state.max_papers,  # 从状态获取
    ...
)
```

**需要修改**:

1. **状态模型** (`src/core/state_models.py`):
```python
class PaperAgentState(BaseModel):
    user_request: str
    max_papers: int = Field(default=10, description="最大论文数量")  # 改为 10
    ...
```

2. **前端输入** (`web/src/views/HomeView.vue`):
```vue
<template>
  <div class="search-config">
    <input v-model="query" placeholder="输入研究主题..." />
    <div class="config-row">
      <label>论文数量:</label>
      <input
        type="number"
        v-model.number="maxPapers"
        min="1"
        max="50"
        value="10"
      />
    </div>
  </div>
</template>
```

3. **API 参数** (`main.py`):
```python
@app.get("/api/research")
async def research(
    query: str,
    max_papers: int = Query(default=10, ge=1, le=50),  # 添加参数
    ...
):
    state = PaperAgentState(
        user_request=query,
        max_papers=max_papers,
        ...
    )
```

---

### 3.2 环节可折叠/展开 + 流式输出

**当前 SSE 数据格式**:
```json
{
  "step": "searching",
  "state": "initializing | thinking | generating | completed",
  "data": "..."
}
```

**目标数据格式**:
```json
{
  "step": "searching",
  "state": "running",
  "summary": "正在搜索论文...",
  "detail": "使用关键词: transformer, medical image segmentation...",
  "stream_content": "找到论文 1/10: ...",  // 流式内容
  "progress": 50,  // 进度百分比
  "collapsible": true,
  "default_collapsed": false
}
```

**实现方案**:

1. **创建可折叠组件** (`web/src/components/CollapsibleStep.vue`):
```vue
<template>
  <div class="step-card" :class="{ collapsed: isCollapsed }">
    <div class="step-header" @click="toggle">
      <span class="step-icon">{{ icon }}</span>
      <span class="step-name">{{ stepName }}</span>
      <span class="step-status">{{ status }}</span>
      <button class="toggle-btn">{{ isCollapsed ? '▼' : '▲' }}</button>
    </div>
    <div v-show="!isCollapsed" class="step-content">
      <div class="summary">{{ summary }}</div>
      <div class="stream-output" v-html="streamContent"></div>
    </div>
  </div>
</template>
```

2. **修改 SSE 推送逻辑** (`src/nodes/*.py`):
```python
# 在每个节点中，分阶段推送状态
async def search_node(state: State) -> State:
    # 初始化阶段
    await state_queue.put(BackToFrontData(
        step=ExecutionState.SEARCHING,
        state="initializing",
        summary="正在初始化搜索...",
        detail="准备搜索参数和连接...",
        collapsible=True,
        default_collapsed=False
    ))

    # 关键词生成阶段
    await state_queue.put(BackToFrontData(
        step=ExecutionState.SEARCHING,
        state="generating",
        summary="正在生成搜索关键词...",
        stream_content="识别到关键概念: Transformer...",
        collapsible=True
    ))

    # 用户审核阶段
    await state_queue.put(BackToFrontData(
        step=ExecutionState.SEARCHING,
        state="user_review",
        summary="等待用户审核搜索关键词",
        detail=json.dumps({"querys": [...], "start_date": ...}),
        collapsible=False  # 审核环节不允许折叠
    ))
```

---

### 3.3 知识库随机命名

**实现方案**:

1. **创建命名生成器** (`src/utils/name_generator.py`):
```python
import random
from datetime import datetime

ACADEMIC_THEMES = [
    "深度学习", "自然语言处理", "计算机视觉", "强化学习",
    "知识图谱", "量子计算", "边缘计算", "联邦学习",
    "生成式 AI", "多模态学习", "图神经网络", "Transformer"
]

ADJECTIVES = ["智能", "先进", "创新", "专业", "学术", "研究"]

def generate_knowledge_base_name(style: str = "academic") -> str:
    """生成随机知识库名称"""
    timestamp = datetime.now().strftime("%m%d")

    if style == "academic":
        theme = random.choice(ACADEMIC_THEMES)
        return f"{theme}研究_{timestamp}"
    elif style == "random":
        adj = random.choice(ADJECTIVES)
        theme = random.choice(ACADEMIC_THEMES)
        random_id = ''.join(random.choices('0123456789abcdef', k=4))
        return f"{adj}{theme}_{random_id}"
    elif style == "timestamp":
        return f"知识库_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        return f"KB_{timestamp}_{random.randint(1000, 9999)}"
```

2. **前端修改** (`web/src/components/CreateDatabaseModal.vue`):
```vue
<template>
  <div class="form-group">
    <label>Name <span class="required">*</span></label>
    <div class="input-with-action">
      <input v-model="formData.name" type="text" />
      <button @click="generateRandomName" class="random-btn">
        🎲 随机生成
      </button>
    </div>
    <div class="name-styles">
      <button @click="generateName('academic')">学术风</button>
      <button @click="generateName('random')">随机风</button>
      <button @click="generateName('timestamp')">时间戳</button>
    </div>
  </div>
</template>

<script>
const generateRandomName = async () => {
  const response = await fetch('/api/knowledge/generate-name')
  const { name } = await response.json()
  formData.name = name
}
</script>
```

---

### 3.4 文档解析支持

**需要添加的依赖** (`pyproject.toml`):
```toml
[tool.poetry.dependencies]
pypdf2 = "^3.0.0"           # PDF 解析
pdfplumber = "^0.10.0"      # PDF 表格解析（可选）
python-docx = "^0.8.11"     # Word 解析
markdown = "^3.5.0"         # Markdown 解析
python-magic = "^0.4.27"    # 文件类型检测
```

**实现方案**:

1. **创建解析模块** (`src/parsers/`):
```python
# src/parsers/__init__.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional
import magic

class DocumentParser(ABC):
    """文档解析器基类"""

    @abstractmethod
    async def parse(self, file_path: str) -> str:
        """解析文档返回纯文本内容"""
        pass

    @abstractmethod
    def supports(self, mime_type: str, file_extension: str) -> bool:
        """是否支持该文件类型"""
        pass

    async def parse_with_metadata(self, file_path: str) -> dict:
        """解析并返回带元数据的结果"""
        content = await self.parse(file_path)
        return {
            "content": content,
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "file_size": Path(file_path).stat().st_size,
            "parser_type": self.__class__.__name__,
            "success": True
        }


# src/parsers/pdf_parser.py
import PyPDF2

class PDFParser(DocumentParser):
    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() == '.pdf'

    async def parse(self, file_path: str) -> str:
        text_parts = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")
        return "\n\n".join(text_parts)


# src/parsers/docx_parser.py
from docx import Document

class DocxParser(DocumentParser):
    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() in ['.docx']

    async def parse(self, file_path: str) -> str:
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)


# src/parsers/markdown_parser.py
import markdown
from bs4 import BeautifulSoup

class MarkdownParser(DocumentParser):
    def supports(self, mime_type: str, file_extension: str) -> bool:
        return file_extension.lower() in ['.md', '.markdown']

    async def parse(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        # 转换为 HTML 后提取纯文本
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n')


# src/parsers/factory.py
class ParserFactory:
    _parsers = [
        PDFParser(),
        DocxParser(),
        MarkdownParser(),
        TextParser(),  # 纯文本
    ]

    @classmethod
    def get_parser(cls, file_path: str) -> DocumentParser:
        mime_type = magic.from_file(file_path, mime=True)
        file_ext = Path(file_path).suffix.lower()

        for parser in cls._parsers:
            if parser.supports(mime_type, file_ext):
                return parser

        raise UnsupportedFormatError(
            f"不支持的文件格式: {file_ext} ({mime_type})"
        )

    @classmethod
    def get_supported_types(cls) -> list:
        return ['.pdf', '.docx', '.md', '.txt', '.markdown']
```

2. **修改上传接口** (`src/knowledge/knowledge_router.py`):
```python
from src.parsers import ParserFactory

@knowledge.post("/databases/{db_id}/documents")
async def add_documents(
    db_id: str,
    items: list[str] = Body(...),
    params: dict = Body(...)
):
    content_type = params.get("content_type", "file")

    if content_type == "file":
        processed_items = []
        for item in items:
            # 解析文件
            try:
                parser = ParserFactory.get_parser(item)
                result = await parser.parse_with_metadata(item)

                # 存储解析结果
                await knowledge_base.add_content(
                    db_id,
                    [result["content"]],  # 使用解析后的文本
                    params={
                        **params,
                        "metadata": {
                            "original_file": item,
                            "file_name": result["file_name"],
                            "parser_type": result["parser_type"]
                        }
                    }
                )
                processed_items.append({
                    "file": item,
                    "status": "success",
                    "parsed_length": len(result["content"])
                })
            except Exception as e:
                processed_items.append({
                    "file": item,
                    "status": "failed",
                    "error": str(e)
                })

        return {
            "db_id": db_id,
            "processed": len(processed_items),
            "success": len([p for p in processed_items if p["status"] == "success"]),
            "failed": len([p for p in processed_items if p["status"] == "failed"]),
            "items": processed_items
        }
```

---

## 4. 数据模型优化建议

### 4.1 添加数据库层

**当前问题**: 所有数据存储在内存或文件系统，无法持久化任务状态

**建议**: 添加 SQLite 作为轻量级持久化

```python
# src/db/models.py
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String(36), primary_key=True)  # UUID
    user_request = Column(Text, nullable=False)
    max_papers = Column(Integer, default=10)
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    current_step = Column(String(50))
    progress = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    report_path = Column(String(500))
    error_message = Column(Text)
    config = Column(JSON)

class StepLog(Base):
    __tablename__ = 'step_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(36), nullable=False, index=True)
    step_name = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # initializing, running, completed, failed
    summary = Column(Text)
    detail = Column(Text)
    stream_content = Column(Text)  # 流式输出内容
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    __table_args__ = (
        # 每个任务的每个步骤只保留最新记录
        UniqueConstraint('task_id', 'step_name', name='uix_task_step'),
    )
```

### 4.2 状态模型扩展

```python
# src/core/state_models.py

class StepState(BaseModel):
    """单个环节的状态"""
    name: str
    status: str  # initializing, running, user_review, completed, failed
    summary: Optional[str] = None
    detail: Optional[str] = None
    stream_content: Optional[str] = None  # 累计流式输出
    progress: int = 0  # 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    collapsible: bool = True
    is_collapsed: bool = False

class PaperAgentState(BaseModel):
    """工作流全局状态（扩展版）"""
    # 用户输入
    user_request: str
    max_papers: int = Field(default=10, ge=1, le=50)

    # 执行状态
    current_step: ExecutionState = Field(default=ExecutionState.INITIALIZING)
    steps: Dict[str, StepState] = Field(default_factory=dict)  # 所有环节状态

    # 各节点数据
    search_results: Optional[List[Dict[str, Any]]] = None
    extracted_data: Optional[ExtractedPapersData] = None
    analyse_results: Optional[str] = None
    writted_sections: Optional[List[str]] = None
    report_markdown: Optional[str] = None

    # 错误信息
    error: NodeError = Field(default_factory=NodeError)

    # 配置
    config: Dict[str, Any] = Field(default_factory=dict)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 5. 前端状态管理建议

### 5.1 添加 Pinia Store

```typescript
// web/src/stores/workflow.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useWorkflowStore = defineStore('workflow', () => {
  // State
  const currentTask = ref(null)
  const steps = ref({})
  const isConnected = ref(false)
  const eventSource = ref(null)

  // Getters
  const currentStep = computed(() => {
    if (!currentTask.value) return null
    return steps.value[currentTask.value.current_step]
  })

  const completedSteps = computed(() => {
    return Object.values(steps.value).filter(s => s.status === 'completed')
  })

  const isRunning = computed(() => {
    return currentTask.value?.status === 'running'
  })

  // Actions
  function initTask(query, maxPapers = 10) {
    currentTask.value = {
      id: generateUUID(),
      query,
      max_papers: maxPapers,
      status: 'initializing',
      current_step: 'initializing',
      created_at: new Date()
    }
    steps.value = {}
  }

  function updateStep(stepName, stepData) {
    if (!steps.value[stepName]) {
      steps.value[stepName] = {
        name: stepName,
        status: 'initializing',
        stream_content: '',
        progress: 0
      }
    }

    // 合并更新
    steps.value[stepName] = {
      ...steps.value[stepName],
      ...stepData
    }

    // 累积流式内容
    if (stepData.stream_chunk) {
      steps.value[stepName].stream_content += stepData.stream_chunk
    }
  }

  function toggleStepCollapse(stepName) {
    if (steps.value[stepName]) {
      steps.value[stepName].is_collapsed = !steps.value[stepName].is_collapsed
    }
  }

  async function startWorkflow() {
    // 初始化 SSE 连接
    eventSource.value = new EventSource(
      `/api/research?query=${encodeURIComponent(currentTask.value.query)}&max_papers=${currentTask.value.max_papers}`
    )

    eventSource.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleSSEMessage(data)
    }

    isConnected.value = true
  }

  function handleSSEMessage(data) {
    updateStep(data.step, {
      status: data.state,
      summary: data.summary,
      detail: data.detail,
      stream_chunk: data.stream_content,
      progress: data.progress,
      collapsible: data.collapsible,
      is_collapsed: data.default_collapsed
    })

    if (data.step === 'finished') {
      closeConnection()
    }
  }

  function closeConnection() {
    if (eventSource.value) {
      eventSource.value.close()
      eventSource.value = null
    }
    isConnected.value = false
  }

  return {
    currentTask,
    steps,
    isConnected,
    currentStep,
    completedSteps,
    isRunning,
    initTask,
    updateStep,
    toggleStepCollapse,
    startWorkflow,
    closeConnection
  }
})
```

---

## 6. 测试策略

### 6.1 单元测试

```python
# tests/test_parsers.py
import pytest
from src.parsers import ParserFactory, PDFParser, DocxParser

class TestPDFParser:
    def test_parse_simple_pdf(self, tmp_path):
        # 创建测试 PDF
        pdf_path = tmp_path / "test.pdf"
        # ... 创建测试文件

        parser = PDFParser()
        content = parser.parse(str(pdf_path))

        assert isinstance(content, str)
        assert len(content) > 0

    def test_parse_invalid_pdf(self, tmp_path):
        parser = PDFParser()
        with pytest.raises(ParseError):
            parser.parse(str(tmp_path / "invalid.pdf"))

class TestNameGenerator:
    def test_generate_academic_name(self):
        from src.utils.name_generator import generate_knowledge_base_name

        name = generate_knowledge_base_name("academic")
        assert "_" in name
        assert len(name) > 0

    def test_no_duplicate_names(self):
        names = [generate_knowledge_base_name("random") for _ in range(100)]
        assert len(names) == len(set(names))
```

### 6.2 集成测试

```python
# tests/test_search_workflow.py
@pytest.mark.asyncio
async def test_search_with_custom_max_papers(client):
    response = await client.get("/api/research?query=transformer&max_papers=15")
    assert response.status_code == 200

    # 验证返回的 SSE 流
    # 验证状态包含 max_papers=15
```

---

## 7. 部署建议

### 7.1 开发环境

```bash
# 1. 安装新依赖
poetry add pypdf2 pdfplumber python-docx markdown python-magic

# 2. 数据库迁移（如果使用 SQLAlchemy）
alembic init migrations
alembic revision --autogenerate -m "init"
alembic upgrade head

# 3. 启动服务
poetry run python -m uvicorn main:app --reload
```

### 7.2 生产环境

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖（pdfplumber 需要）
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY . .

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. 总结

### 8.1 短期目标（2 周内）
1. ✅ 完成搜索论文数量可配置
2. ✅ 完成环节可折叠/展开
3. ✅ 完成知识库随机命名
4. ✅ 完成 PDF/Word/Markdown 文档解析

### 8.2 中期目标（4 周内）
1. 添加数据库持久化
2. 实现任务历史与重试
3. 完善错误处理机制
4. 添加配置持久化

### 8.3 长期目标（8 周内）
1. 实现限流与并发控制
2. 移动端适配
3. 性能优化
4. 完整的测试覆盖

---

**文档维护**: 随着开发进度持续更新此文档，标记已完成项并添加新的技术决策。
