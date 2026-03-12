# Findings - Paper Analysis Agent 技术调研

**项目**: Paper Analysis Agent
**创建时间**: 2026-03-11

---

## 1. 现有架构调研

### 1.1 后端技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | FastAPI | ^0.116.1 | REST API + SSE |
| 工作流 | LangGraph | ^0.6.7 | 状态机编排 |
| 智能体 | AutoGen | ^0.2.20 | 多智能体协作 |
| 向量库 | ChromaDB | ^1.0.20 | 知识库存储 |
| 依赖管理 | Poetry | - | Python 包管理 |

### 1.2 前端技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 框架 | Vue 3 | ^3.4.0 | 响应式 UI |
| 路由 | Vue Router | ^4.4.0 | 页面路由 |
| 构建 | Vite | ^5.0.0 | 开发服务器 |
| HTTP | Axios | ^1.7.0 | API 请求 |

### 1.3 SSE 数据格式 (Current)

```json
{
  "step": "searching|reading|analysing|writing|reporting",
  "state": "initializing|thinking|generating|user_review|completed|error|finished",
  "data": "..."
}
```

**发现**: 当前 `data` 字段是字符串类型，需要扩展为结构化数据以支持折叠面板。

---

## 2. 文档解析库调研

### 2.1 可用库对比

| 格式 | 候选库 | 优点 | 缺点 | 选择 |
|------|--------|------|------|------|
| PDF | PyPDF2 | 轻量、纯 Python | 复杂排版解析弱 | ✅ 选用 |
| PDF | pdfplumber | 表格解析强 | 依赖多、较重 | 备选 |
| Word | python-docx | 标准库、稳定 | 仅支持 .docx | ✅ 选用 |
| Markdown | markdown | 标准转换 | 需配合 BeautifulSoup | ✅ 选用 |
| Text | 内置 | 无需额外依赖 | - | ✅ 选用 |

### 2.2 pyproject.toml 现有依赖检查

已存在的相关依赖：
- `pymupdf = "^1.26.4"` - PDF 处理（fitz）
- `python-docx = "^1.2.0"` - Word 处理
- `markdown = "^3.10.2"` - Markdown 处理
- `beautifulsoup4 = "^4.14.3"` - HTML 解析

**发现**: 所需依赖基本已安装，只需添加 `pypdf2` 作为备选或检查 `pymupdf` 是否足够。

---

## 3. 状态模型调研

### 3.1 当前 PaperAgentState

```python
class PaperAgentState(BaseModel):
    user_request: str
    current_step: ExecutionState
    search_results: Optional[List[Dict]]
    extracted_data: Optional[ExtractedPapersData]
    analyse_results: Optional[str]
    writted_sections: Optional[List[str]]
    report_markdown: Optional[str]
    error: NodeError
```

**缺失字段**:
- `max_papers: int` - 搜索数量配置
- `step_states: Dict[str, StepState]` - 各环节详细状态

### 3.2 建议扩展的 BackToFrontData

```python
class BackToFrontData(BaseModel):
    step: str
    state: str
    data: Any = None
    # 新增字段:
    summary: Optional[str] = None      # 环节摘要
    detail: Optional[str] = None       # 详细内容
    stream_content: Optional[str] = None  # 流式片段
    progress: int = 0                  # 进度百分比
    collapsible: bool = True           # 是否可折叠
    default_collapsed: bool = False    # 默认折叠状态
```

---

## 4. 命名生成策略调研

### 4.1 随机命名风格

| 风格 | 示例 | 适用场景 |
|------|------|----------|
| 学术风 | "深度学习研究_0311" | 正式研究 |
| 随机风 | "智能文档库_a3f9" | 快速创建 |
| 时间戳 | "KB_20250311_143052" | 精确标识 |
| 主题+ID | "量子计算_8f2d" | 主题明确 |

### 4.2 去重策略

1. 添加 4 位随机十六进制后缀（65536 种可能）
2. 必要时添加时间戳
3. 检查现有知识库名称避免重复

---

## 5. API 接口调研

### 5.1 现有接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/research?query=...` | 启动调研 (SSE) |
| POST | `/send_input` | 提交审核结果 |
| GET | `/api/reports` | 历史报告列表 |
| GET/PUT/DELETE | `/api/reports/{filename}` | 报告 CRUD |
| GET/POST | `/knowledge/...` | 知识库管理 |

### 5.2 需要新增接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/generate-name?style=...` | 生成随机知识库名 |

### 5.3 需要修改接口

| 方法 | 路径 | 变更 |
|------|------|------|
| GET | `/api/research` | 添加 `max_papers` 参数 |

---

## 6. 前端组件调研

### 6.1 现有组件

- `CreateDatabaseModal.vue` - 创建知识库弹窗
- `FileUpload.vue` - 文件上传
- `HomeView.vue` - 主页（查询输入）
- `History.vue` - 历史报告
- `KnowledgeBase.vue` - 知识库管理

### 6.2 需要新增组件

- `CollapsibleStep.vue` - 可折叠环节卡片
- `StepProgress.vue` - 环节进度展示（可选）

### 6.3 状态管理

当前：组件级 reactive state
建议：添加 Pinia Store 管理全局工作流状态，特别是折叠状态

---

## 7. 实施顺序建议

基于依赖关系和实施复杂度：

```
Phase 1: FR-004 (搜索数量配置)
    - 改动范围小，快速见效
    - 为后续测试提供便利

Phase 3: FR-007 (知识库随机命名)
    - 独立功能，可并行开发
    - 改动范围小

Phase 2: FR-005 (环节折叠展示)
    - 涉及前后端数据格式变更
    - 为 FR-006 打基础

Phase 4: FR-008 (文档解析)
    - 独立功能，改动较大
    - 可并行于 Phase 2/3

Phase 5: FR-006 (流式输出)
    - 依赖 Phase 2
    - 增强用户体验
```

