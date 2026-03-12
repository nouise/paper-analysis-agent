# Paper Analysis Agent - 需求文档 (RPD)

**版本**: 1.0
**日期**: 2026-03-11
**状态**: 进行中

---

## 1. 项目概述

Paper Analysis Agent 是一个基于多智能体协作的学术论文调研系统。用户输入研究主题，系统自动完成**论文检索 → 论文阅读 → 聚类分析 → 分章写作 → 报告生成**的全流程，输出结构完整的 Markdown 调研报告。

### 1.1 目标用户
- **学术研究人员**: 需要快速了解某研究领域的现状和趋势
- **企业研发人员**: 需要调研技术方案和研究方向
- **学生/研究生**: 需要撰写文献综述和开题报告

### 1.2 核心价值主张
在 10 分钟内完成传统需要数天的文献调研工作，并提供可编辑、可发布的专业报告。

---

## 2. 功能需求

### 2.1 核心工作流（已完成）

#### FR-001: 论文搜索 [已完成]
**用户故事**: 作为用户，我希望能输入研究主题后自动搜索相关论文，以便获取资料

**验收标准**:
1. WHEN 用户输入自然语言查询 THEN 系统 SHALL 使用 LLM 提取结构化搜索条件
2. WHEN 生成搜索关键词 THEN 系统 SHALL 推送至前端供用户审核
3. WHEN 用户确认或修改搜索条件 THEN 系统 SHALL 调用 arXiv API 搜索论文
4. WHEN 搜索完成 THEN 系统 SHALL 返回论文列表（标题、作者、摘要、链接等）
5. WHEN 搜索失败 THEN 系统 SHALL 重试最多 2 次并返回错误信息

**边界条件**:
- WHEN 搜索返回 0 篇论文 THEN 系统 SHALL 提示"未找到相关论文"
- WHEN arXiv API 不可用时 THEN 系统 SHALL 返回错误并记录日志

---

#### FR-002: 论文阅读与分析 [已完成]
**用户故事**: 作为用户，我希望系统自动阅读并分析论文，以便提取关键信息

**验收标准**:
1. WHEN 获取论文列表 THEN 系统 SHALL 并行阅读所有论文
2. WHEN 阅读单篇论文 THEN 系统 SHALL 提取：核心问题、关键方法、数据集、评估指标、主要结果、局限性、贡献
3. WHEN 提取完成 THEN 系统 SHALL 将结果存入 ChromaDB 向量数据库
4. WHEN 所有论文阅读完成 THEN 系统 SHALL 进行聚类分析
5. WHEN 聚类完成 THEN 系统 SHALL 生成全局分析报告

---

#### FR-003: 报告生成 [已完成]
**用户故事**: 作为用户，我希望获得结构化的调研报告，以便直接使用或发布

**验收标准**:
1. WHEN 分析完成 THEN 系统 SHALL 生成报告大纲
2. WHEN 大纲生成 THEN 系统 SHALL 拆分为多个写作子任务并行执行
3. WHEN 写作完成 THEN 系统 SHALL 组装完整 Markdown 报告
4. WHEN 报告生成 THEN 系统 SHALL 保存到 `output/reports/` 目录
5. WHEN 报告生成 THEN 系统 SHALL 支持一键转换为微信公众号格式

---

### 2.2 搜索配置（待开发）

#### FR-004: 可配置搜索论文数量 [P0]
**用户故事**: 作为用户，我希望能够自定义搜索的论文数量，以便控制调研范围和成本

**验收标准**:
1. WHEN 用户输入查询时 THEN 系统 SHALL 提供输入框设置论文数量（1-50）
2. WHEN 用户未设置数量 THEN 系统 SHALL 使用默认值 10
3. WHEN 用户设置数量超出范围 THEN 系统 SHALL 自动调整为边界值
4. WHEN 搜索执行时 THEN 系统 SHALL 使用用户指定的数量调用 API
5. WHEN 搜索结果返回 THEN 系统 SHALL 显示实际获取的论文数量

**边界条件**:
- WHEN arXiv API 返回数量少于请求 THEN 系统 SHALL 返回实际获取的论文并提示
- WHEN 用户设置数量为 0 或负数 THEN 系统 SHALL 使用默认值

**技术实现建议**:
- 前端：在查询输入界面添加数量选择器（Slider 或 Number Input）
- 后端：修改 `SearchQuery` 模型，添加 `max_results` 字段
- 修改 `PaperSearcher.search_papers()` 方法接收该参数

---

### 2.3 流式输出展示（待开发）

#### FR-005: 可折叠/展开的环节输出 [P0]
**用户故事**: 作为用户，我希望能够查看每个处理环节的详细输出，并可以折叠/展开，以便更好地了解处理过程

**验收标准**:
1. WHEN 系统进入新环节（搜索/阅读/分析/写作/报告）THEN 系统 SHALL 在界面显示该环节卡片
2. WHEN 环节正在执行时 THEN 系统 SHALL 显示加载动画和当前状态
3. WHEN 环节完成时 THEN 系统 SHALL 显示完成状态和关键结果摘要
4. WHEN 用户点击展开按钮 THEN 系统 SHALL 显示该环节的详细输出内容
5. WHEN 用户点击折叠按钮 THEN 系统 SHALL 隐藏详细内容仅显示摘要
6. WHEN 多个环节完成时 THEN 系统 SHALL 允许独立控制每个环节的展开/折叠状态

**技术实现建议**:
- 前端：使用 Collapse/Accordion 组件展示各环节
- 数据结构：每个环节包含 `summary`（摘要）和 `details`（详情）
- SSE 推送：实时推送各环节的状态和输出

---

#### FR-006: 流式内容实时显示 [P1]
**用户故事**: 作为用户，我希望能够实时看到 LLM 生成的内容，以便了解处理进度

**验收标准**:
1. WHEN LLM 生成内容时 THEN 系统 SHALL 通过 SSE 实时推送生成的文本片段
2. WHEN 前端接收片段 THEN 系统 SHALL 实时追加显示到对应区域
3. WHEN 用户折叠了某环节 THEN 系统 SHALL 继续接收但不显示详细内容
4. WHEN 生成完成 THEN 系统 SHALL 标记该环节为完成状态

---

### 2.4 知识库增强（待开发）

#### FR-007: 知识库随机命名 [P0]
**用户故事**: 作为用户，我希望创建知识库时可以随机生成名字，以便快速创建而不必费心命名

**验收标准**:
1. WHEN 用户打开创建知识库弹窗 THEN 系统 SHALL 提供"随机生成名称"按钮
2. WHEN 用户点击随机生成 THEN 系统 SHALL 生成有意义的随机名称（如："量子计算研究_20250311"或"AI伦理探索"）
3. WHEN 随机名称生成 THEN 系统 SHALL 允许用户修改
4. WHEN 用户提交 THEN 系统 SHALL 使用最终确认的名称创建知识库
5. WHEN 生成随机名称 THEN 系统 SHALL 避免与现有知识库名称重复

**随机命名策略**:
- 学术主题 + 随机数字（如："深度学习研究_8472"）
- 形容词 + 名词 + ID（如："智能文档库_a3f9"）
- 时间戳命名（如："KB_20250311_143052"）
- 可配置：允许用户选择命名风格

---

#### FR-008: 文档解析支持 [P0]
**用户故事**: 作为用户，我希望上传 PDF/Word 等文档后能自动解析内容，以便建立知识库

**验收标准**:
1. WHEN 用户上传 PDF 文件 THEN 系统 SHALL 提取文本内容
2. WHEN 用户上传 Word (.docx) 文件 THEN 系统 SHALL 提取文本内容
3. WHEN 用户上传 Markdown 文件 THEN 系统 SHALL 保留格式并提取内容
4. WHEN 用户上传 TXT 文件 THEN 系统 SHALL 直接读取内容
5. WHEN 文档解析完成 THEN 系统 SHALL 将内容分块并建立向量索引
6. WHEN 文档包含图片 THEN 系统 SHALL 可选提取图片 OCR 文本（如配置了 OCR）
7. WHEN 解析失败 THEN 系统 SHALL 返回具体错误信息（如：文件损坏、格式不支持）

**支持的文件格式**:
| 格式 | 扩展名 | 优先级 | 状态 |
|------|--------|--------|------|
| PDF | .pdf | P0 | 待实现 |
| Word | .docx | P0 | 待实现 |
| Markdown | .md | P0 | 待实现 |
| Text | .txt | P0 | 待实现 |
| Word (旧) | .doc | P1 | 待实现 |
| HTML | .html | P1 | 待实现 |
| EPUB | .epub | P2 | 待实现 |

**技术实现建议**:
- PDF: 使用 `PyPDF2` 或 `pdfplumber`
- Word: 使用 `python-docx`
- Markdown: 使用 `markdown` 库转换为文本
- 统一接口：`DocumentParser` 类，根据文件类型选择对应解析器

---

#### FR-009: 知识库文档管理 [P1]
**用户故事**: 作为用户，我希望能够管理知识库中的文档，以便查看、删除或重新索引

**验收标准**:
1. WHEN 用户进入知识库详情 THEN 系统 SHALL 显示该知识库中的所有文档列表
2. WHEN 显示文档列表 THEN 系统 SHALL 显示文档名称、上传时间、文件大小、解析状态
3. WHEN 用户点击文档 THEN 系统 SHALL 显示文档预览（前 500 字）
4. WHEN 用户删除文档 THEN 系统 SHALL 从知识库中移除该文档及其向量
5. WHEN 用户重新索引 THEN 系统 SHALL 重新解析并建立索引

---

### 2.5 生产就绪功能（待开发）

#### FR-010: 用户配置持久化 [P1]
**用户故事**: 作为用户，我希望我的设置能够被保存，以便下次使用时无需重新配置

**验收标准**:
1. WHEN 用户修改默认搜索数量 THEN 系统 SHALL 保存到用户配置
2. WHEN 用户选择模型 THEN 系统 SHALL 保存模型偏好
3. WHEN 用户返回系统 THEN 系统 SHALL 自动加载之前的配置
4. WHEN 配置加载失败 THEN 系统 SHALL 使用系统默认值

---

#### FR-011: 任务历史与重试 [P1]
**用户故事**: 作为用户，我希望能够查看历史任务并重新执行，以便复用之前的查询

**验收标准**:
1. WHEN 任务完成或失败 THEN 系统 SHALL 保存任务记录到历史
2. WHEN 用户进入历史页面 THEN 系统 SHALL 显示所有任务列表
3. WHEN 用户点击"重新执行" THEN 系统 SHALL 使用相同参数启动新任务
4. WHEN 任务失败 THEN 系统 SHALL 提供"重试"按钮从失败环节继续

---

#### FR-012: 错误处理与恢复 [P1]
**用户故事**: 作为用户，当某个环节失败时，我希望能够知道原因并选择重试或跳过

**验收标准**:
1. WHEN 某环节失败 THEN 系统 SHALL 显示错误信息和可能原因
2. WHEN 错误发生时 THEN 系统 SHALL 提供"重试该环节"按钮
3. WHEN 用户点击跳过时 THEN 系统 SHALL 继续执行后续环节（使用默认值或空值）
4. WHEN 网络错误发生时 THEN 系统 SHALL 自动重试 3 次

---

#### FR-013: 并发控制与限流 [P2]
**用户故事**: 作为系统管理员，我希望控制并发任务数量，以便保证系统稳定性

**验收标准**:
1. WHEN 并发任务超过阈值 THEN 系统 SHALL 将新任务放入队列等待
2. WHEN 任务在队列中 THEN 系统 SHALL 通知用户当前排队位置
3. WHEN API 调用频率达到上限 THEN 系统 SHALL 自动限流并等待

---

## 3. 非功能需求

### 3.1 性能需求

| ID | 需求描述 | 目标值 | 优先级 |
|----|----------|--------|--------|
| NFR-001 | 搜索响应时间 | < 5 秒 | P0 |
| NFR-002 | 单篇论文阅读时间 | < 10 秒 | P0 |
| NFR-003 | 完整报告生成时间 | < 10 分钟（20篇论文） | P0 |
| NFR-004 | 前端首屏加载时间 | < 3 秒 | P1 |
| NFR-005 | 支持的最大论文数量 | 50 篇 | P1 |
| NFR-006 | 同时在线用户数 | 50 人 | P2 |

### 3.2 安全需求

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| NFR-007 | API Key 不得硬编码，使用环境变量 | P0 |
| NFR-008 | 用户上传文件需验证类型和大小 | P0 |
| NFR-009 | 文件路径需验证防止目录遍历攻击 | P0 |
| NFR-010 | 敏感操作需记录审计日志 | P1 |

### 3.3 可用性需求

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| NFR-011 | 系统可用性 | 99.5% | P1 |
| NFR-012 | 支持离线查看已生成报告 | P1 |
| NFR-013 | 移动端适配 | P2 |

### 3.4 可维护性需求

| ID | 需求描述 | 优先级 |
|----|----------|--------|
| NFR-014 | 代码测试覆盖率 | > 60% | P1 |
| NFR-015 | API 文档完整 | P1 |
| NFR-016 | 错误日志可追踪 | P0 |

---

## 4. 优先级矩阵

### P0 - 必须完成（MVP）
- [x] FR-001: 论文搜索
- [x] FR-002: 论文阅读与分析
- [x] FR-003: 报告生成
- [ ] FR-004: 可配置搜索论文数量
- [ ] FR-005: 可折叠/展开的环节输出
- [ ] FR-007: 知识库随机命名
- [ ] FR-008: 文档解析支持

### P1 - 应该完成
- [ ] FR-006: 流式内容实时显示
- [ ] FR-009: 知识库文档管理
- [ ] FR-010: 用户配置持久化
- [ ] FR-011: 任务历史与重试
- [ ] FR-012: 错误处理与恢复

### P2 - 可以完成
- [ ] FR-013: 并发控制与限流
- [ ] 移动端适配
- [ ] 多语言支持

---

## 5. 技术架构建议

### 5.1 当前架构评估

**优势**:
- LangGraph + AutoGen 提供了良好的工作流编排能力
- SSE 实时推送用户体验良好
- ChromaDB 向量检索高效

**待优化**:
- 缺少持久化层（目前报告仅存为文件）
- 缺少任务队列管理
- 前端状态管理待完善

### 5.2 建议改进

#### 5.2.1 添加数据库层（SQLite/PostgreSQL）
```sql
-- 任务表
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    user_request TEXT NOT NULL,
    max_papers INTEGER DEFAULT 10,
    status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_path TEXT,
    error_message TEXT
);

-- 环节日志表
CREATE TABLE step_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT REFERENCES tasks(id),
    step_name TEXT NOT NULL,
    status TEXT,
    summary TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户配置表
CREATE TABLE user_configs (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5.2.2 文档解析服务
```python
# src/parsers/__init__.py
from abc import ABC, abstractmethod
from typing import BinaryIO

class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, file_path: str) -> str:
        """解析文档返回文本内容"""
        pass

    @abstractmethod
    def supports(self, file_extension: str) -> bool:
        """是否支持该文件类型"""
        pass

# 具体实现
class PDFParser(DocumentParser): ...
class DocxParser(DocumentParser): ...
class MarkdownParser(DocumentParser): ...

# 工厂
class ParserFactory:
    _parsers = [PDFParser(), DocxParser(), MarkdownParser(), TextParser()]

    @classmethod
    def get_parser(cls, file_path: str) -> DocumentParser:
        ext = Path(file_path).suffix.lower()
        for parser in cls._parsers:
            if parser.supports(ext):
                return parser
        raise UnsupportedFormatError(f"不支持的格式: {ext}")
```

#### 5.2.3 前端组件结构
```
web/src/components/
├── workflow/               # 工作流展示组件
│   ├── WorkflowPanel.vue   # 主面板
│   ├── StepCard.vue        # 单环节卡片（可折叠）
│   └── StepDetail.vue      # 环节详情
├── knowledge/              # 知识库组件
│   ├── KnowledgeCard.vue
│   ├── DocumentList.vue
│   └── DocumentPreview.vue
└── common/                 # 通用组件
    ├── CollapsePanel.vue
    ├── NumberInput.vue
    └── RandomNameGenerator.vue
```

---

## 6. 验收测试计划

### 6.1 测试场景

#### 场景 1: 完整工作流
1. 输入查询 "Transformer 架构在医学图像分割中的应用"
2. 设置论文数量为 10
3. 审核并确认搜索关键词
4. 等待系统完成所有环节
5. 验证报告生成并下载

#### 场景 2: 知识库管理
1. 创建知识库（使用随机名称）
2. 上传 PDF 文档
3. 验证文档解析成功
4. 测试查询功能
5. 删除文档并验证

#### 场景 3: 环节展示
1. 启动任务
2. 验证各环节卡片按顺序出现
3. 点击展开查看详细输出
4. 验证折叠后状态保持
5. 验证实时流式输出

### 6.2 性能测试
- 并发测试：同时启动 5 个任务
- 压力测试：搜索 50 篇论文的完整流程
- 长时间运行测试：连续运行 24 小时

---

## 7. 发布计划

### Phase 1 - MVP (2 周)
- 完成 FR-004: 可配置搜索数量
- 完成 FR-005: 可折叠环节输出
- 完成 FR-007: 知识库随机命名
- 完成 FR-008: 基础文档解析（PDF、Word、MD）

### Phase 2 - 增强 (2 周)
- 完成 FR-006: 流式内容实时显示
- 完成 FR-009: 知识库文档管理
- 完成 FR-010: 用户配置持久化
- 添加数据库层

### Phase 3 - 生产就绪 (2 周)
- 完成 FR-011: 任务历史与重试
- 完成 FR-012: 错误处理与恢复
- 完成 NFR: 性能优化
- 添加完整测试覆盖

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| SSE | Server-Sent Events，服务器推送技术 |
| RAG | Retrieval-Augmented Generation，检索增强生成 |
| LangGraph | 用于构建状态化多智能体工作流的框架 |
| AutoGen | 微软开源的多智能体对话框架 |
| ChromaDB | 开源向量数据库 |

### 8.2 外部依赖

| 服务 | 用途 | 替代方案 |
|------|------|----------|
| arXiv API | 论文搜索 | Semantic Scholar API |
| DashScope | LLM 调用 | OpenAI、SiliconFlow |
| ChromaDB | 向量存储 | Pinecone、Weaviate |

### 8.3 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| arXiv API 限流 | 高 | 实现重试机制和本地缓存 |
| LLM API 成本高 | 中 | 添加用量限制和成本预估 |
| 文档解析准确性 | 中 | 使用多种解析库对比，允许用户修正 |

---

**文档维护**: 本需求文档应随着项目进展持续更新，每次变更需记录变更日志。

**变更日志**:
| 日期 | 版本 | 变更内容 | 作者 |
|------|------|----------|------|
| 2026-03-11 | 1.0 | 初始版本 | Claude |
