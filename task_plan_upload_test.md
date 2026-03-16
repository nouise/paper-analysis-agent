# Task Plan: 测试文件上传到知识库流程

## Goal
模拟测试 PDF 上传并添加到知识库的完整流程，找出前端无反应的原因。

## Current Phase
Phase 1: 诊断上传流程问题

## Phases

### Phase 1: 检查服务和端口
**目标**: 确认前后端服务正常运行
**状态**: in_progress

**检查项**:
- [ ] 1.1 确认后端服务运行 (port 8003)
- [ ] 1.2 确认前端服务运行 (port 5180)
- [ ] 1.3 测试后端上传 API
- [ ] 1.4 测试前端控制台错误

### Phase 2: 模拟文件上传流程
**目标**: 用 Playwright 模拟完整上传流程
**状态**: pending

**任务**:
- [ ] 2.1 创建测试 PDF 文件
- [ ] 2.2 模拟点击知识库卡片
- [ ] 2.3 模拟上传文件
- [ ] 2.4 检查控制台错误
- [ ] 2.5 截图记录流程

### Phase 3: 后端 API 测试
**目标**: 直接测试后端上传 API
**状态**: pending

**任务**:
- [ ] 3.1 测试 /knowledge/files/upload
- [ ] 3.2 测试 /knowledge/databases/{db_id}/documents
- [ ] 3.3 检查响应数据

### Phase 4: 修复问题
**目标**: 根据测试结果修复问题
**状态**: ✅ complete

**发现的问题**:
1. ❌ FileUpload.vue 缺少 `formatFileSize` 方法
   - 错误: `Property "formatFileSize" was accessed during render but is not defined`
   - 修复: 添加 `formatFileSize` 函数

2. ❌ "Add to KB" 按钮不显示
   - 原因: Vue 的 `v-else-if` 是互斥的，前面的 "uploaded" 状态 span 匹配后，后面的 button 不会渲染
   - 修复: 将 button 的 `v-else-if` 改为 `v-if`

**修复文件**:
- `web/src/components/FileUpload.vue`
  - 添加 `formatFileSize` 方法
  - 修复 button 的 `v-if` 条件

---

### Phase 5: 验证修复
**目标**: 重新测试验证
**状态**: ✅ complete

**测试结果**:
- ✅ 文件上传成功 (test_upload.txt, 171.0 B)
- ✅ "Add to KB" 按钮正确显示
- ✅ 点击 "Add to KB" 后状态变为 "Adding..."
- ✅ 流程正常工作

**截图记录**:
- debug_01_initial.png - 初始页面
- debug_02_selected.png - 选择知识库
- debug_03_after_upload.png - 上传完成
- debug_04_queue.png - 显示 "Add to KB" 按钮
- debug_05_after_add.png - 点击后 "Adding..."

---

## 问题根因总结

| 问题 | 原因 | 修复 |
|------|------|------|
| 上传后无反应 | `formatFileSize` 方法未定义导致渲染错误 | 添加方法 |
| "Add to KB" 按钮不显示 | Vue `v-else-if` 互斥导致 | 改为 `v-if` |

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| `formatFileSize is not a function` | 1 | 添加 formatFileSize 方法 |
| "Add to KB" button not showing | 1 | 将 v-else-if 改为 v-if |


---

## Key Questions
1. 前端是否有控制台错误？
2. 后端 API 是否正常响应？
3. 文件上传后是否显示 Add to KB 按钮？
4. 点击 Add to KB 后是否有反应？

---

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| 待记录 | - | - |
