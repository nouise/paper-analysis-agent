# WeChat Studio 优化 - Findings & Decisions

## Requirements
从用户请求中提取的三个核心需求：
1. **流式输出** - AI 回复实时显示，让用户及时看到反馈
2. **导出笔记** - 将对话内容整理成公众号笔记，支持模板选择
3. **多格式导出** - 支持导出 PDF、HTML，以及发布到公众号

## Research Findings

### 流式输出实现方案
- **后端现状**: `/api/chat` 已支持流式输出，使用 `EventSourceResponse` 返回 SSE 格式
- **前端现状**: 已有 streaming UI 结构，但使用的是非流式 API
- **技术选择**: 使用 `fetch` + `ReadableStream` 而不是 `EventSource`
  - 原因：`EventSource` 只支持 GET 请求，而我们需要 POST 请求发送消息历史
  - 实现：使用 `response.body.getReader()` 读取流式数据

### 导出笔记功能设计
- **消息选择**: 支持多选/单选 AI 消息，用户可以整合多次对话内容
- **模板系统**: 提供 5 种模板
  - 技术文章 (article): 适合技术分享和教程
  - 读书笔记 (notes): 整理阅读笔记和要点
  - 访谈记录 (interview): 问答形式的访谈内容
  - 新闻简报 (news): 简洁的新闻摘要格式
  - 对话总结 (summary): 总结对话要点

### 导出格式实现
- **Markdown**: 前端直接下载，无需后端支持
- **HTML**: 前端下载，复用已有的 previewHtml
- **PDF**: 后端使用 Playwright 生成，需要额外依赖
  - 方案对比:
    - WeasyPrint: 纯 Python，但 CSS 支持有限
    - Playwright: 支持完整 CSS，但需要安装 Chromium
    - 选择 Playwright: 可以保持与 HTML 预览一致的样式

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| 使用 fetch + ReadableStream | EventSource 不支持 POST，fetch 可以发送消息历史 |
| 5 种导出模板 | 覆盖常见内容场景（技术/阅读/访谈/新闻/总结） |
| PDF 使用 Playwright | 保持与 HTML 预览一致的样式，支持完整 CSS |
| 导出对话框使用 Teleport | 避免 z-index 问题，确保对话框在全屏遮罩之上 |
| 消息选择使用 Set | 高效处理多选，支持快速添加/删除 |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| SSE 格式不统一 | 后端统一返回 `data: {json}\n\n` 格式 |
| 流式数据解析 | 前端添加缓冲处理，支持跨 chunk 的 JSON |

## Resources
- WeChatEditor.vue: 主要前端组件
- main.py: 后端 API
- Playwright PDF: https://playwright.dev/python/

## Visual/Browser Findings
- 用户截图显示 WeChat Studio 界面分为左右两部分：
  - 左侧：AI 对话区域
  - 右侧：Note Editor 编辑区域
- 当前已有基础导出功能（Export 按钮）
- 需要增强：消息选择、模板选择、多格式导出

## Implementation Notes

### 流式输出关键代码
```javascript
const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  const chunk = decoder.decode(value, { stream: true })
  // 处理 SSE 格式 data: {...}
}
```

### 导出对话框关键代码
```vue
<Teleport to="body">
  <div v-if="showExportDialog" class="export-dialog-overlay">
    <!-- 模板选择 -->
    <div class="template-grid">
      <div v-for="template in exportTemplates" :key="template.id">
        <!-- 模板卡片 -->
      </div>
    </div>
    <!-- 消息选择 -->
    <div class="messages-list-select">
      <!-- 可选择的 AI 消息 -->
    </div>
  </div>
</Teleport>
```

### PDF 导出 API
```python
@app.post('/api/wechat/export-pdf')
async def export_to_pdf(data: WeChatExportPDFRequest):
    # 1. Markdown -> HTML
    # 2. Playwright 渲染并生成 PDF
    # 3. 返回 PDF 下载链接
```

## Security Considerations
- PDF 导出使用 Playwright 的 Chromium，确保沙箱安全
- 导出内容经过 DOMPurify 净化（前端已有）
- 所有 API 端点都有适当的错误处理
