# Task Plan: WeChat Studio 优化

## Goal
优化 WeChat Studio 界面，实现：1) AI 流式输出显示；2) 增强导出笔记功能（支持模板选择）；3) 支持导出 PDF、HTML、发布到公众号。

## Current Phase
Phase 1

## Phases

### Phase 1: Requirements & Discovery
- [x] 分析现有 WeChatEditor.vue 代码结构
- [x] 分析后端 /api/chat 流式 API 实现
- [x] 分析 wechat_service 现有功能
- [x] 理解用户三个核心需求
- **Status:** complete

### Phase 2: Planning & Structure
- [x] 设计流式输出前端架构 (EventSource)
- [x] 设计笔记导出功能（消息选择、模板选择）
- [x] 设计导出功能架构（PDF、HTML、公众号）
- [x] 规划文件修改清单
- **Status:** in_progress

### Phase 3: Implementation - 流式输出
- [x] 修改 WeChatEditor.vue 使用 EventSource 接收流式数据
- [x] 更新 sendMessage 方法支持流式显示
- [x] 测试流式输出功能
- **Status:** pending

### Phase 4: Implementation - 导出笔记功能
- [x] 添加消息选择功能（多选/单选）
- [x] 添加模板选择器组件
- [x] 实现智能内容提取和格式化
- [x] 将选中内容填充到 Note Editor
- **Status:** pending

### Phase 5: Implementation - 导出功能
- [x] 添加导出格式选择（PDF、HTML、Markdown）
- [x] 实现 PDF 导出 API（后端）
- [x] 实现 HTML 导出 API（后端）
- [x] 集成公众号发布功能
- **Status:** pending

### Phase 6: Testing & Verification
- [x] 验证流式输出正常工作
- [x] 验证导出笔记功能完整
- [x] 验证 PDF/HTML 导出可用
- [x] 验证公众号发布流程
- **Status:** pending

### Phase 7: Delivery
- [x] 代码审查和优化
- [x] 功能演示
- **Status:** pending

## Key Questions
1. 流式输出使用 SSE 还是 WebSocket？→ SSE (EventSource) 更简单，后端已支持
2. 笔记模板有哪些类型？→ 技术文章、读书笔记、访谈记录、新闻简报
3. PDF 导出如何生成？→ 使用 Python 库如 WeasyPrint 或 markdown-pdf

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 使用 EventSource (SSE) 实现流式 | 后端 /api/chat 已支持 SSE，无需额外改动 |
| 前端直接渲染流式内容 | 用户可以看到实时生成的内容，体验更好 |
| 导出时支持选择多条消息 | 用户可能想要整合多次对话的内容 |
| 添加模板选择器 | 不同场景（技术/访谈/笔记）需要不同格式 |
| PDF 导出使用 Playwright + Paged.js | 可以保持与 HTML 预览一致的样式 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- 后端 /api/chat 已支持流式输出，通过 stream=true 参数
- WeChatEditor.vue 已有 streaming UI 结构，只需连接真实流式数据
- exportFromChat 功能需要增强，支持选择消息和模板
- 导出功能需要新增后端 API
