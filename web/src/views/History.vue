<template>
  <div class="history-container">
    <div class="page-header">
      <h1>历史报告</h1>
      <div class="header-actions">
        <button class="btn-refresh" @click="loadHistory" :disabled="isLoading">
          🔄 刷新
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-state" v-if="isLoading">
      <div class="spinner"></div>
      <p>加载历史报告...</p>
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else-if="historyList.length === 0 && !selectedReport">
      <div class="empty-icon">📋</div>
      <p>暂无历史报告</p>
      <button class="btn-create" @click="goToCreate">创建第一个报告</button>
    </div>

    <!-- 报告详情视图 -->
    <div class="report-detail" v-if="selectedReport">
      <div class="detail-header">
        <button class="btn-back" @click="closeReport">← 返回列表</button>
        <div class="detail-actions">
          <button class="btn-toggle-edit" @click="toggleEdit" :class="{ active: isEditing }">
            {{ isEditing ? '📖 预览' : '✏️ 编辑' }}
          </button>
          <button class="btn-save" v-if="isEditing && isModified" @click="saveReport">
            💾 保存
          </button>
          <button class="btn-copy" @click="copyReport">📋 复制</button>
          <button class="btn-wechat" @click="showWechatModal = true">📱 微信公众号</button>
        </div>
      </div>

      <div class="detail-meta">
        <span class="meta-tag">📅 {{ selectedReport.created_at }}</span>
        <span class="meta-tag">🔍 {{ selectedReport.query }}</span>
        <span class="meta-tag warning" v-if="isModified">⚠️ 未保存</span>
      </div>

      <!-- 编辑模式 -->
      <div class="editor-container" v-if="isEditing">
        <textarea
          v-model="editContent"
          class="markdown-editor"
          spellcheck="false"
          @input="isModified = true"
        ></textarea>
      </div>

      <!-- 预览模式 -->
      <div class="preview-container markdown-body" v-else v-html="renderedMarkdown"></div>
    </div>

    <!-- 微信公众号转换弹窗 -->
    <div class="modal-overlay" v-if="showWechatModal" @click="closeWechatModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>📱 转换为微信公众号格式</h2>
          <button class="btn-close" @click="closeWechatModal">✕</button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>主题风格</label>
            <select v-model="wechatTheme" class="form-select">
              <option value="tech">科技风 (蓝紫渐变)</option>
              <option value="minimal">简约风 (黑白灰)</option>
              <option value="business">商务风 (深蓝金色)</option>
            </select>
          </div>

          <div class="form-group">
            <label>作者</label>
            <input v-model="wechatAuthor" type="text" class="form-input" placeholder="Paper Agent" />
          </div>

          <div class="preview-info">
            <p>💡 转换后的 HTML 将保存到 <code>output/wechat/</code> 目录</p>
            <p>📋 你可以在浏览器中预览，然后复制粘贴到微信公众号编辑器</p>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeWechatModal">取消</button>
          <button class="btn-primary" @click="convertToWechat" :disabled="isConverting">
            {{ isConverting ? '转换中...' : '🔄 转换为 HTML' }}
          </button>
          <button class="btn-success" @click="publishToWechat" :disabled="isPublishing">
            {{ isPublishing ? '发布中...' : '🚀 一键发布到微信' }}
          </button>
        </div>
      </div>
    </div>

    <!-- HTML 预览弹窗 -->
    <div class="modal-overlay" v-if="showHtmlPreview" @click="closeHtmlPreview">
      <div class="modal-content modal-large" @click.stop>
        <div class="modal-header">
          <h2>📄 HTML 预览</h2>
          <button class="btn-close" @click="closeHtmlPreview">✕</button>
        </div>

        <div class="modal-body">
          <div class="html-preview-actions">
            <button class="btn-copy-html" @click="copyHtmlContent">📋 复制 HTML</button>
            <button class="btn-open-file" @click="openHtmlFile">🌐 在浏览器中打开</button>
          </div>
          <div class="html-preview-container" v-html="previewHtmlContent"></div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeHtmlPreview">关闭</button>
        </div>
      </div>
    </div>

    <!-- 报告列表 -->
    <div class="history-list" v-if="!selectedReport && historyList.length > 0">
      <div
        v-for="item in historyList"
        :key="item.filename"
        class="history-card"
      >
        <div class="card-header">
          <div class="report-title">
            <span class="report-icon">📄</span>
            <span class="title-text">{{ item.title }}</span>
          </div>
        </div>

        <div class="card-content">
          <div class="report-query">
            <span class="label">查询内容:</span>
            <span class="content">{{ item.query }}</span>
          </div>

          <div class="report-meta">
            <div class="meta-item">
              <span class="meta-icon">📅</span>
              <span class="meta-text">{{ item.created_at }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-icon">📏</span>
              <span class="meta-text">{{ formatSize(item.size) }}</span>
            </div>
          </div>
        </div>

        <div class="card-actions">
          <button class="btn-view" @click="viewReport(item)">👁️ 查看详情</button>
          <button class="btn-delete" @click="deleteReport(item)">🗑️ 删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const router = useRouter()

const isLoading = ref(false)
const historyList = ref([])
const selectedReport = ref(null)
const editContent = ref('')
const isEditing = ref(false)
const isModified = ref(false)

// 微信公众号相关
const showWechatModal = ref(false)
const wechatTheme = ref('tech')
const wechatAuthor = ref('Paper Agent')
const isConverting = ref(false)
const isPublishing = ref(false)
const showHtmlPreview = ref(false)
const previewHtmlContent = ref('')
const currentHtmlPath = ref('')

const renderedMarkdown = computed(() => {
  const content = isEditing.value ? editContent.value : (selectedReport.value?.content || '')
  if (!content) return ''
  return DOMPurify.sanitize(marked.parse(content))
})

const loadHistory = async () => {
  isLoading.value = true
  try {
    const res = await fetch('/api/reports')
    if (!res.ok) throw new Error('加载失败')
    historyList.value = await res.json()
  } catch (error) {
    console.error('加载历史报告失败:', error)
    historyList.value = []
  } finally {
    isLoading.value = false
  }
}

const viewReport = async (item) => {
  isLoading.value = true
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(item.filename)}`)
    if (!res.ok) throw new Error('加载报告失败')
    selectedReport.value = await res.json()
    editContent.value = selectedReport.value.content
    isEditing.value = false
    isModified.value = false
  } catch (error) {
    console.error('加载报告详情失败:', error)
    alert('加载报告失败，请重试')
  } finally {
    isLoading.value = false
  }
}

const toggleEdit = () => {
  isEditing.value = !isEditing.value
}

const saveReport = async () => {
  if (!selectedReport.value) return
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(selectedReport.value.filename)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: editContent.value })
    })
    if (!res.ok) throw new Error('保存失败')
    selectedReport.value.content = editContent.value
    isModified.value = false
    alert('保存成功')
  } catch (error) {
    console.error('保存报告失败:', error)
    alert('保存失败，请重试')
  }
}

const copyReport = () => {
  const content = editContent.value || selectedReport.value?.content || ''
  navigator.clipboard.writeText(content)
  alert('已复制到剪贴板')
}

const deleteReport = async (item) => {
  if (!confirm(`确定要删除报告"${item.title}"吗？此操作不可恢复。`)) return
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(item.filename)}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('删除失败')
    historyList.value = historyList.value.filter(h => h.filename !== item.filename)
  } catch (error) {
    console.error('删除报告失败:', error)
    alert('删除失败，请重试')
  }
}

const closeReport = () => {
  if (isModified.value && !confirm('有未保存的修改，确定返回吗？')) return
  selectedReport.value = null
  isEditing.value = false
  isModified.value = false
}

const formatSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const goToCreate = () => {
  router.push('/')
}

// 微信公众号功能
const closeWechatModal = () => {
  showWechatModal.value = false
}

const convertToWechat = async () => {
  if (!selectedReport.value) return

  isConverting.value = true
  try {
    const res = await fetch('/api/wechat/convert-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedReport.value.filename,
        theme: wechatTheme.value
      })
    })

    if (!res.ok) {
      const error = await res.json()
      throw new Error(error.detail || '转换失败')
    }

    const result = await res.json()
    previewHtmlContent.value = result.html_content
    currentHtmlPath.value = result.html_path

    alert(`✅ 转换成功！\n\n文件已保存到: ${result.html_path}\n\n点击"在浏览器中打开"预览效果`)
    showWechatModal.value = false
    showHtmlPreview.value = true

  } catch (error) {
    console.error('转换失败:', error)
    alert(`转换失败: ${error.message}`)
  } finally {
    isConverting.value = false
  }
}

const publishToWechat = async () => {
  if (!selectedReport.value) return

  if (!confirm('确定要发布到微信公众号草稿箱吗？\n\n请确保已配置微信公众号 AppID 和 AppSecret')) {
    return
  }

  isPublishing.value = true
  try {
    // 先转换为 HTML
    const convertRes = await fetch('/api/wechat/convert-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        filename: selectedReport.value.filename,
        theme: wechatTheme.value
      })
    })

    if (!convertRes.ok) {
      const error = await convertRes.json()
      throw new Error(error.detail || '转换失败')
    }

    const convertResult = await convertRes.json()

    // 发布到微信
    const publishRes = await fetch('/api/wechat/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: selectedReport.value.title,
        html_content: convertResult.html_content,
        author: wechatAuthor.value
      })
    })

    if (!publishRes.ok) {
      const error = await publishRes.json()
      throw new Error(error.detail || '发布失败')
    }

    const publishResult = await publishRes.json()

    alert(`🎉 发布成功！\n\n文章已保存到微信公众号草稿箱\nmedia_id: ${publishResult.result.media_id}\n\n请前往微信公众号后台查看`)
    showWechatModal.value = false

  } catch (error) {
    console.error('发布失败:', error)
    alert(`发布失败: ${error.message}\n\n请检查:\n1. 是否已配置微信公众号凭证\n2. 网络连接是否正常\n3. 查看控制台获取详细错误信息`)
  } finally {
    isPublishing.value = false
  }
}

const closeHtmlPreview = () => {
  showHtmlPreview.value = false
}

const copyHtmlContent = () => {
  navigator.clipboard.writeText(previewHtmlContent.value)
  alert('✅ HTML 内容已复制到剪贴板\n\n你可以直接粘贴到微信公众号编辑器')
}

const openHtmlFile = () => {
  if (currentHtmlPath.value) {
    alert(`请在文件管理器中打开:\n${currentHtmlPath.value}\n\n然后用浏览器打开该文件`)
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e9ecef;
}

.page-header h1 {
  margin: 0;
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 600;
  color: #2c3e50;
}

.btn-refresh {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  background: #2980b9;
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
  color: #6c757d;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80px 20px;
  background: #f8f9fa;
  border-radius: 12px;
  color: #6c757d;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 0 0 20px 0;
  font-size: 16px;
}

.btn-create {
  background: #3498db;
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create:hover {
  background: #2980b9;
}

/* 报告列表 */
.history-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.history-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #e9ecef;
}

.history-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.card-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e9ecef;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.report-icon { font-size: 20px; }

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-content { margin-bottom: 16px; }

.report-query { margin-bottom: 12px; }

.report-query .label {
  display: block;
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 4px;
}

.report-query .content {
  display: block;
  font-size: 14px;
  color: #2c3e50;
  line-height: 1.5;
  word-break: break-word;
}

.report-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6c757d;
}

.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

.btn-view, .btn-delete {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-view {
  background: #e3f2fd;
  color: #3498db;
}

.btn-view:hover {
  background: #3498db;
  color: white;
}

.btn-delete {
  background: #f8f9fa;
  color: #dc3545;
  border: 1px solid #e9ecef;
}

.btn-delete:hover {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

/* 报告详情 */
.report-detail {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  flex-wrap: wrap;
  gap: 12px;
}

.btn-back {
  padding: 8px 16px;
  background: none;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  color: #495057;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.btn-back:hover {
  background: #e9ecef;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.btn-toggle-edit, .btn-save, .btn-copy {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-toggle-edit {
  background: #e3f2fd;
  color: #3498db;
}

.btn-toggle-edit.active {
  background: #3498db;
  color: white;
}

.btn-save {
  background: #27ae60;
  color: white;
}

.btn-save:hover {
  background: #219653;
}

.btn-copy {
  background: #f0f0f0;
  color: #555;
}

.btn-copy:hover {
  background: #ddd;
}

.btn-wechat {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #07c160;
  color: white;
}

.btn-wechat:hover {
  background: #06ad56;
  transform: translateY(-1px);
}

.detail-meta {
  display: flex;
  gap: 12px;
  padding: 12px 24px;
  background: #fafbfc;
  border-bottom: 1px solid #e9ecef;
  flex-wrap: wrap;
}

.meta-tag {
  font-size: 13px;
  color: #6c757d;
  background: #e9ecef;
  padding: 4px 12px;
  border-radius: 12px;
}

.meta-tag.warning {
  background: #fff3cd;
  color: #856404;
}

/* 编辑器 */
.editor-container {
  padding: 0;
}

.markdown-editor {
  width: 100%;
  min-height: 600px;
  padding: 24px;
  border: none;
  outline: none;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  box-sizing: border-box;
  background: #fefefe;
}

.markdown-editor:focus {
  background: #fffff8;
}

/* 预览 */
.preview-container {
  padding: 24px 32px;
  min-height: 400px;
}

/* Markdown 渲染样式 */
.markdown-body {
  line-height: 1.7;
  color: #2d3748;
  word-break: break-word;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: #1a202c;
}

.markdown-body h1 { font-size: 2em; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }
.markdown-body h2 { font-size: 1.5em; border-bottom: 1px solid #edf2f7; padding-bottom: 6px; }
.markdown-body h3 { font-size: 1.25em; }

.markdown-body p { margin-top: 0; margin-bottom: 16px; }

.markdown-body ul, .markdown-body ol {
  padding-left: 2em;
  margin-bottom: 16px;
}

.markdown-body strong { font-weight: 600; }

.markdown-body code {
  padding: 0.2em 0.4em;
  background: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-size: 85%;
}

.markdown-body blockquote {
  padding: 0 1em;
  color: #6a737d;
  border-left: 4px solid #dfe2e5;
  margin: 0 0 16px 0;
}

.markdown-body a {
  color: #3498db;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.markdown-body hr {
  border: none;
  border-top: 2px solid #e2e8f0;
  margin: 24px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .history-container { padding: 15px; }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .history-list { grid-template-columns: 1fr; }
  .detail-header { flex-direction: column; }
  .detail-actions { width: 100%; justify-content: flex-end; }
  .preview-container { padding: 16px; }
  .markdown-editor { padding: 16px; min-height: 400px; }
}

@media (max-width: 480px) {
  .history-container { padding: 12px; }
  .page-header h1 { font-size: 24px; }
  .history-card { padding: 16px; }
  .card-actions { flex-direction: column; }
}

/* 微信公众号弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: auto;
}

.modal-large {
  max-width: 900px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  color: #6c757d;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-close:hover {
  background: #f8f9fa;
  color: #2c3e50;
}

.modal-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
}

.form-select, .form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  font-size: 14px;
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-select:focus, .form-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.preview-info {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
}

.preview-info p {
  margin: 8px 0;
  font-size: 13px;
  color: #6c757d;
  line-height: 1.6;
}

.preview-info code {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', monospace;
  font-size: 12px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e9ecef;
}

.btn-primary, .btn-secondary, .btn-success {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-secondary {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.btn-secondary:hover {
  background: #e9ecef;
}

.btn-success {
  background: #07c160;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #06ad56;
}

.btn-primary:disabled, .btn-success:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

/* HTML 预览样式 */
.html-preview-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.btn-copy-html, .btn-open-file {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-copy-html {
  background: #3498db;
  color: white;
}

.btn-copy-html:hover {
  background: #2980b9;
}

.btn-open-file {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #dee2e6;
}

.btn-open-file:hover {
  background: #e9ecef;
}

.html-preview-container {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 20px;
  background: #fafbfc;
  max-height: 500px;
  overflow: auto;
}

</style>
