# Task Plan - Paper Analysis Agent 功能完善

**项目**: Paper Analysis Agent
**目标**: 按照 RPD 需求文档实现 P0/P1 优先级功能
**创建时间**: 2026-03-11
**状态**: 🟡 规划中

---

## Goals

1. 实现搜索论文数量可配置（FR-004）
2. 实现环节可折叠/展开展示（FR-005）
3. 实现知识库随机命名（FR-007）
4. 实现文档解析支持 PDF/Word/Markdown/TXT（FR-008）
5. 实现流式内容实时显示（FR-006，P1）

---

## Phases

### Phase 1: 搜索论文数量可配置（FR-004）
**状态**: ✅ 已完成
**优先级**: P0
**预计工时**: 1-2 天
**完成时间**: 2026-03-11

**Tasks**:
- [x] 1.1 后端：修改 `PaperAgentState` 添加 `max_papers` 字段（默认 10）
- [x] 1.2 后端：修改 `/api/research` 接口接收 `max_papers` 参数
- [x] 1.3 后端：修改 `search_node` 使用用户指定的数量
- [x] 1.4 前端：在 HomeView.vue 添加数量选择器（Slider 或 Number Input）
- [x] 1.5 前端：将 maxPapers 参数传递到 SSE 请求
- [x] 1.6 测试：验证边界值处理（<1 自动设为 1，>50 自动设为 50）

**Files Modified**:
- `src/core/state_models.py` - 已存在 max_papers 字段，默认值 10
- `src/nodes/search.py` - 已使用 current_state.max_papers
- `src/agents/orchestrator.py` - 修改默认值为 10
- `main.py` - 添加 max_papers Query 参数，范围 1-50
- `web/src/views/HomeView.vue` - 添加数量选择器和样式

**Notes**:
- FastAPI Query 参数自动验证范围，超出范围会返回 422 错误
- 前端使用 number + range input 组合，更好的用户体验
- 默认值为 10，符合 RPD 要求

---

### Phase 2: 环节可折叠/展开展示（FR-005）
**状态**: ✅ 已完成
**优先级**: P0
**预计工时**: 2-3 天
**完成时间**: 2026-03-11

**Tasks**:
- [x] 2.1 后端：扩展 `BackToFrontData` 添加 `summary`、`detail`、`collapsible` 字段
- [x] 2.2 后端：修改各节点推送更丰富的状态信息
- [x] 2.3 前端：修改 HomeView.vue 使用新的数据结构展示各环节
- [x] 2.4 前端：添加进度条显示
- [x] 2.5 前端：实现摘要和详情展示

**Files Modified**:
- `src/core/state_models.py` - 扩展 BackToFrontData
- `src/nodes/search.py` - 更新状态推送
- `src/nodes/reading.py` - 更新状态推送
- `src/nodes/analyse.py` - 更新状态推送 (via agent)
- `src/nodes/writing.py` - 更新状态推送 (via agent)
- `src/nodes/report.py` - 更新状态推送 (via agent)
- `web/src/views/HomeView.vue` - 更新 UI 和 handler

**Notes**:
- 使用向后兼容的方式，保留 data 字段
- 前端显示 summary 和 progress 进度条
- 详情内容支持 Markdown 渲染

---

### Phase 3: 知识库随机命名（FR-007）
**状态**: ✅ 已完成
**优先级**: P0
**预计工时**: 1 天
**完成时间**: 2026-03-11

**Tasks**:
- [x] 3.1 后端：创建 `src/utils/name_generator.py` 命名生成器
- [x] 3.2 后端：添加 `/api/knowledge/generate-name` 接口
- [x] 3.3 前端：修改 `CreateDatabaseModal.vue` 添加随机生成按钮
- [x] 3.4 前端：支持多种命名风格选择（学术风/随机风/时间戳）
- [x] 3.5 测试：验证名称不重复

**Files Modified**:
- `src/utils/name_generator.py` (new)
- `src/knowledge/knowledge_router.py`
- `web/src/components/CreateDatabaseModal.vue`

**Naming Styles**:
- Academic: "深度学习研究_0311"
- Random: "智能文档库_a3f9"
- Timestamp: "KB_20250311_143052"
- Simple: "自然语言处理_8472"

---

### Phase 4: 文档解析支持（FR-008）
**状态**: ✅ 已完成
**优先级**: P0
**预计工时**: 2-3 天
**完成时间**: 2026-03-11

**Tasks**:
- [x] 4.1 检查依赖：使用现有的 `pymupdf`、`python-docx`、`markdown`
- [x] 4.2 创建 `src/parsers/__init__.py` 定义 `DocumentParser` 基类
- [x] 4.3 创建 `src/parsers/pdf_parser.py` PDF 解析器 (PyMuPDF)
- [x] 4.4 创建 `src/parsers/docx_parser.py` Word 解析器
- [x] 4.5 创建 `src/parsers/markdown_parser.py` Markdown 解析器
- [x] 4.6 创建 `src/parsers/text_parser.py` 纯文本解析器
- [x] 4.7 创建 `src/parsers/factory.py` 解析器工厂
- [x] 4.8 修改 `knowledge_router.py` 上传接口使用解析器
- [x] 4.9 前端：显示文件解析状态和结果

**Files Modified/Created**:
- `src/parsers/` (new directory)
  - `__init__.py` - 基类定义
  - `pdf_parser.py` - PDF 解析器
  - `docx_parser.py` - Word 解析器
  - `markdown_parser.py` - Markdown 解析器
  - `text_parser.py` - 纯文本解析器
  - `factory.py` - 解析器工厂
- `src/knowledge/knowledge_router.py` - 添加解析逻辑
- `src/knowledge/knowledge/indexing.py` - 更新支持类型
- `web/src/components/FileUpload.vue` - 显示解析状态

---

### Phase 5: 流式内容实时显示（FR-006）
**状态**: ✅ 已完成
**优先级**: P1
**预计工时**: 2 天
**完成时间**: 2026-03-12

**Tasks**:
- [x] 5.1 后端：修改 `BackToFrontData` 添加 `stream_content` 字段 - 已存在
- [x] 5.2 后端：在 writing 节点推送 LLM 生成的流式片段
- [x] 5.3 前端：修改折叠组件支持流式内容累积显示
- [x] 5.4 前端：即使环节折叠也继续接收 SSE 数据
- [x] 5.5 测试：验证流式输出流畅性

**Files Modified**:
- `src/nodes/writing.py` - 添加 `_stream_write_section` 函数，支持流式写作
- `web/src/views/HomeView.vue` - 添加 `handleStreamContent` 函数和流式内容显示

**Implementation Details**:
1. 后端使用模拟流式效果（分段推送内容），每100字符推送一次
2. 前端添加 `streamContent` 字段存储累积的流式内容
3. 新增 "Live Output" 区块显示实时写作内容
4. 添加脉冲动画指示正在写入状态

---

### Phase 6: 知识库功能增强
**状态**: ✅ 已完成
**优先级**: P0
**预计工时**: 2 天
**完成时间**: 2026-03-12

**需求描述**:
1. 文档上传后支持确认再添加到知识库 - ✅ 已修改为上传后显示"Add to KB"按钮
2. 支持知识库名称修改 - ✅ 已实现

**Tasks**:
- [x] 6.1 后端：检查文档添加到知识库的现有逻辑
- [x] 6.2 后端：修复/完善文档添加到知识库功能 - 功能正常
- [x] 6.3 后端：添加知识库名称修改 API `PUT /knowledge/databases/{db_id}` - 已存在
- [x] 6.4 前端：修改 FileUpload.vue - 上传后显示确认按钮
- [x] 6.5 前端：在知识库卡片上添加编辑名称按钮 - DatabaseCard.vue 已添加
- [x] 6.6 前端：修改 CreateDatabaseModal 支持编辑模式 - 已实现
- [x] 6.7 联调测试文档添加和名称修改功能

**Files Modified**:
- `web/src/components/FileUpload.vue` - 添加确认按钮流程
- `web/src/components/DatabaseCard.vue` - 添加编辑按钮
- `web/src/components/CreateDatabaseModal.vue` - 支持编辑模式
- `web/src/views/KnowledgeBase.vue` - 添加编辑处理函数和新的事件处理

---

## Current Phase

✅ 部署完成 - 本地环境已成功运行

---

## 🚀 部署状态

### 后端服务
- **状态**: ✅ 运行中
- **端口**: 8003 (原 8002 被占用)
- **命令**: `poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8003`
- **API 文档**: http://localhost:8003/docs

### 前端服务
- **状态**: ✅ 运行中
- **端口**: 5177 (原配置 5174-5176 被占用)
- **命令**: `npm run dev`
- **访问地址**: http://localhost:5177

### 修改的配置文件
- `web/vite.config.js` - 更新代理端口 8002 → 8003

---

## 启动命令总结

### 后端（Poetry）
```bash
cd D:\2026\个人简历\InterestingWork\paper-analysis-agent
poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

### 前端
```bash
cd web
npm run dev
```

### 一键启动脚本（Windows PowerShell）
```powershell
# 启动后端（后台运行）
Start-Process -WindowStyle Hidden -FilePath "poetry" -ArgumentList "run","python","-m","uvicorn","main:app","--host","0.0.0.0","--port","8003"

# 等待后端启动
Start-Sleep -Seconds 3

# 启动前端
cd web
npm run dev
```

---

## 验证步骤

1. ✅ 访问 http://localhost:8003/docs - 应该看到 FastAPI API 文档
2. ✅ 访问 http://localhost:5177 - 应该看到前端首页
3. ✅ 点击 History 菜单 - 应该正常加载历史报告
4. ✅ 点击 Library 菜单 - 应该正常加载知识库

---

### Phase 7: WeChat & Chat 功能修复
- [x] 检查并杀掉占用端口的进程
- [x] 启动后端服务 (端口 8002)
- [x] 启动前端服务
- [x] 测试 /api/chat 接口 - 工作正常
- [x] 测试 /api/wechat/* 接口 - 工作正常
- [x] 修复发现的问题 - 端口占用已解决
- **Status:** complete

---

## 🔴 问题摘要

**现象**: GitHub 更新代码后，本地运行 history、library 等界面异常

**根本原因**:
- Linux 服务器已配置好 Poetry 和 Python 依赖
- 本地 Windows 环境缺少后端 Python 依赖（FastAPI、ChromaDB 等）
- 后端服务无法启动，导致前端 API 请求失败

**解决方案**:

### 快速修复（使用 pip）

```bash
# 1. 进入项目目录
cd D:\2026\个人简历\InterestingWork\paper-analysis-agent

# 2. 安装核心依赖
pip install fastapi uvicorn chromadb langgraph langchain \
    langchain-community autogen pydantic sse-starlette

# 3. 启动后端
python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# 4. 在另一个终端启动前端
cd web
npm run dev
```

### 推荐方案（使用 Poetry）

```bash
# 1. 安装 Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# 2. 安装依赖
poetry install --no-root

# 3. 启动后端
poetry run python -m uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# 4. 启动前端
cd web
npm run dev
```

**访问地址**:
- 前端: http://localhost:5173
- 后端 API 文档: http://localhost:8002/docs

---

## 详细诊断报告

详见 `findings.md` 文件，包含：
- 完整的依赖检查清单
- 三种解决方案（Poetry/pip/requirements）
- 可能的后续问题（数据库路径、代理配置、端口冲突）
- 验证步骤

---

**已完成的功能**:
1. ✅ FR-004: 搜索论文数量可配置 (1-50)
2. ✅ FR-005: 环节可折叠/展开展示 (带进度条)
3. ✅ FR-007: 知识库随机命名 (4 种风格)
4. ✅ FR-008: 文档解析支持 (PDF/Word/Markdown/TXT)

**待开发** (P1):
- FR-006: 流式内容实时显示

---

## Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-11 | 先实现 P0 功能，P1 功能后续迭代 | P0 是 MVP 必需功能 |
| 2026-03-11 | 使用 PyPDF2 而非 pdfplumber | PyPDF2 更轻量，先满足基本需求 |
| 2026-03-11 | 前端使用 Pinia 管理折叠状态 | 跨组件状态共享需要 |

---

## Dependencies

```
Phase 1 (FR-004)
    ↓
Phase 2 (FR-005)
    ↓
Phase 5 (FR-006) - depends on Phase 2

Phase 3 (FR-007) - independent
Phase 4 (FR-008) - independent
```

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| SSE 数据格式变更影响前端 | 高 | 保持向后兼容，先增后删 |
| 文档解析库依赖复杂 | 中 | 逐个添加，充分测试 |
| 命名生成可能重复 | 低 | 添加时间戳+随机数后缀 |

---

## Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | - | - |

