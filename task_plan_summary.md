# Task Plan: WeChat Studio 导出功能增强 - 大模型总结

## Goal
增强 WeChat Studio 导出功能，调用大模型对选中的对话内容进行智能总结，按模板格式输出专业内容。

## Current Phase
Phase 2

## Phases

### Phase 1: Requirements & Discovery
- [x] 分析现有导出功能实现（简单字符串拼接）
- [x] 理解大模型总结需求
- [x] 确定技术方案
- **Status:** complete

### Phase 2: Planning & Design
- [x] 设计5个模板的专业 Prompt
- [x] 设计前端调用大模型的流程
- [x] 确定加载状态和错误处理
- **Status:** complete

### Phase 3: Implementation - Template Prompts
- [x] 技术文章模板 Prompt
- [x] 读书笔记模板 Prompt
- [x] 访谈记录模板 Prompt
- [x] 新闻简报模板 Prompt
- [x] 对话总结模板 Prompt
- **Status:** complete

### Phase 4: Implementation - Frontend Integration
- [x] 修改 confirmExport 支持异步
- [x] 添加大模型 API 调用
- [x] 添加流式显示总结过程
- [x] 添加取消/重试机制
- **Status:** complete

### Phase 5: Testing & Verification
- [ ] 测试各模板总结效果
- [ ] 验证加载状态正常
- [ ] 验证错误处理完善
- **Status:** in_progress

### Phase 6: Delivery
- [ ] 代码审查
- [ ] 功能演示
- **Status:** pending

## Key Questions
1. 如何设计 Prompt 让大模型按模板格式输出？→ 提供明确的格式要求和示例
2. 是否显示总结进度？→ 是，使用流式输出显示
3. 如何处理总结失败？→ 提供重试机制和降级方案

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| 前端直接调用 /api/chat | 复用现有流式接口，无需新增后端 API |
| 每个模板独立 Prompt | 不同模板需要不同的专业格式化要求 |
| 显示"AI 正在整理笔记..." | 让用户了解正在进行智能总结 |
| 提供"原始内容"选项 | 如果总结失败，用户可选择使用原始拼接内容 |

## Template Prompts Design

### 1. 技术文章 (article)
**目标**: 将对话内容整理成结构化的技术文章
**Prompt 要点**:
- 提取技术概念、原理、应用场景
- 按「引言-核心内容-实践建议-总结」结构组织
- 添加小标题和重点标注
- 使用专业术语，保持技术准确性

### 2. 读书笔记 (notes)
**目标**: 提炼书籍/文章的核心观点和启发
**Prompt 要点**:
- 提取3-5个核心观点
- 每个观点配简要说明和个人启发
- 添加「金句摘录」板块
- 使用要点列表形式

### 3. 访谈记录 (interview)
**目标**: 将对话整理成结构化的 Q&A 或观点摘要
**Prompt 要点**:
- 识别问答模式，整理成 Q&A 格式
- 或提取受访者的核心观点
- 添加「核心洞察」板块
- 保持原意，不添加未提及的内容

### 4. 新闻简报 (news)
**目标**: 提取关键信息，形成简洁的新闻摘要
**Prompt 要点**:
- 5W1H（何时、何地、何人、何事、为何、如何）
- 突出新闻价值和影响
- 添加「关键数据/事实」板块
- 使用倒金字塔结构

### 5. 对话总结 (summary)
**目标**: 提炼对话的关键结论和行动建议
**Prompt 要点**:
- 提取关键决策和结论
- 列出行动建议（如有）
- 添加「遗留问题」板块
- 简洁明了，突出重点

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |
