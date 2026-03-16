# Task Plan: 重构 WeChat Editor 为 AI 对话式笔记系统

## Goal
将 WeChat Editor 重构为实用的 **AI 对话式笔记系统**：
1. 类似 Chat 的界面与 AI 对话
2. AI 生成内容可一键导出为笔记
3. 笔记支持编辑修改
4. 笔记可发布到微信公众号

## Current Phase
Phase 3 (Implementation Complete) - Ready for Testing

## Phases

### Phase 1: Requirements & Discovery ✅
- [x] 分析当前 WeChatEditor 设计问题：静态编辑器，无 AI 交互
- [x] 确定新设计方向：Chat 界面 + 笔记管理 + 微信发布
- [x] 确认后端 API：已有 `/api/chat` 或需要新增
- **Status:** complete

### Phase 2: Planning & Structure ✅
- [x] 设计新页面布局：左侧聊天、右侧笔记编辑
- [x] 规划数据流：对话历史 → 导出笔记 → 编辑 → 发布
- [x] 确定组件结构：ChatArea, NoteEditor, PublishPanel
- **Status:** complete

### Phase 3: Implementation ✅
- [x] 重构 WeChatEditor.vue：改为 Chat + Editor 双栏布局
- [x] 添加 AI Chat 功能：消息列表、输入框、流式响应
- [x] 添加导出笔记功能：从对话导出可编辑的 Markdown
- [x] 添加笔记编辑器：支持标题、内容、元数据编辑
- [x] 保留微信发布功能：转换 HTML、发布到草稿箱
- **Status:** complete

### Phase 4: Backend API ✅
- [x] 检查现有 chat API 是否可用
- [x] 新增 `/api/chat` endpoint 支持流式响应
- **Status:** complete

### Phase 5: Testing & Verification 🔄
- [ ] 测试 AI 对话功能
- [ ] 测试导出笔记功能
- [ ] 测试笔记编辑功能
- [ ] 测试发布到微信功能
- **Status:** in_progress

## New Design Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WeChat Studio                            │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│   🤖 AI Chat             │   📝 Note Editor                 │
│   ┌──────────────────┐   │   ┌────────────────────────────┐ │
│   │ Chat Messages    │   │   │ Title: [______________]    │ │
│   │ ─────────────    │   │   │                            │ │
│   │ User: 帮我写一篇  │   │   │ Content:                   │ │
│   │ AI: 好的，这是...│   │   │ ┌────────────────────────┐ │ │
│   │ ─────────────    │   │   │ │ Markdown Editor        │ │ │
│   │ User: 导出笔记   │   │   │ │ ...                    │ │ │
│   │ ─────────────    │   │   │ └────────────────────────┘ │ │
│   │                  │   │   │                            │ │
│   └──────────────────┘   │   │ Theme: [Tech ▼]            │ │
│   ┌──────────────────┐   │   │ Author: [_____]            │ │
│   │ [输入消息...   ] │   │   │                            │ │
│   │ [发送] [导出笔记]│   │   │ [Convert] [Publish]        │ │
│   └──────────────────┘   │   └────────────────────────────┘ │
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

## Key Features

### 1. AI Chat Area (Left Panel)
- 消息气泡列表（用户右对齐，AI 左对齐）
- 输入框 + 发送按钮
- 导出当前对话为笔记按钮
- 清空对话按钮
- 流式响应显示（打字机效果）

### 2. Note Editor (Right Panel)
- 标题输入
- Markdown 内容编辑器
- 主题选择（Tech/Minimal/Business）
- 作者输入
- 摘要输入
- Convert to HTML 按钮
- Publish to WeChat 按钮

### 3. Data Flow
```
User Input → AI Response → Export to Note → Edit → Publish
                ↓
         [Optional: Multiple rounds]
```

## Implementation Summary

### Files Created/Modified

1. **main.py** - 添加 `/api/chat` endpoint
   - 支持流式和非流式响应
   - 使用 DashScope Qwen-max 模型

2. **WeChatEditor.vue** - 完全重写
   - 双栏布局（Chat + Editor）
   - AI 对话流式显示
   - 一键导出功能
   - 主题切换、预览、发布

3. **History.vue** - 添加发布按钮
   - HTML 预览模态框中添加 "Publish to WeChat" 按钮

4. **Sidebar.vue** - 已添加 WeChat 菜单
   - 导航入口已配置

## API Requirements

### Existing APIs
- `POST /api/chat` - AI 对话（新增）
- `POST /api/wechat/convert` - Markdown 转 HTML
- `POST /api/wechat/publish` - 发布到微信
- `POST /api/wechat/convert-and-publish` - 一键转换并发布
- `POST /api/wechat/convert-report` - 转换历史报告

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| 原设计不实用 | 1 | 完全重构为 Chat + Editor 双栏布局 |

## Next Steps
1. 启动后端服务测试 `/api/chat`
2. 启动前端测试完整流程
3. 验证微信发布功能
