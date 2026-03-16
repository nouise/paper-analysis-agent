<template>
  <div class="history-studio">
    <!-- Header -->
    <header class="studio-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-accent">Research</span> History
        </h1>
        <p class="page-subtitle">Browse and manage your previous research reports</p>
      </div>
      <button class="refresh-btn" @click="loadHistory" :disabled="isLoading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ spinning: isLoading }">
          <polyline points="23 4 23 10 17 10"/>
          <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
        </svg>
        Refresh
      </button>
    </header>

    <!-- Content -->
    <div class="content-wrapper">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading history...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="historyList.length === 0 && !selectedReport" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>
        <h3>No Reports Yet</h3>
        <p>Start your first research to see it here</p>
        <button class="primary-btn" @click="goToCreate">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Research
        </button>
      </div>

      <!-- Report Detail View -->
      <div v-else-if="selectedReport" class="detail-view">
        <div class="detail-header">
          <button class="back-btn" @click="closeReport">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="19" y1="12" x2="5" y2="12"/>
              <polyline points="12 19 5 12 12 5"/>
            </svg>
            Back to List
          </button>
          <div class="detail-actions">
            <button class="action-btn" :class="{ active: isEditing }" @click="toggleEdit">
              {{ isEditing ? 'Preview' : 'Edit' }}
            </button>
            <button v-if="isEditing && isModified" class="action-btn primary" @click="saveReport">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/>
                <polyline points="17 21 17 13 7 13 7 21"/>
                <polyline points="7 3 7 8 15 8"/>
              </svg>
              Save
            </button>
            <button class="action-btn" @click="copyReport">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              Copy
            </button>
            <button class="action-btn wechat" @click="showWechatModal = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/>
              </svg>
              WeChat
            </button>
          </div>
        </div>

        <div class="detail-meta">
          <div class="meta-item">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            <span>{{ selectedReport.created_at }}</span>
          </div>
          <div class="meta-item query">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
            <span>{{ selectedReport.query }}</span>
          </div>
          <div v-if="isModified" class="modified-badge">Unsaved Changes</div>
        </div>

        <div class="detail-content">
          <textarea
            v-if="isEditing"
            v-model="editContent"
            class="content-editor"
            spellcheck="false"
            @input="isModified = true"
          ></textarea>
          <div v-else class="content-preview markdown-body" v-html="renderedMarkdown"></div>
        </div>
      </div>

      <!-- Reports Grid -->
      <div v-else class="reports-grid">
        <div
          v-for="item in historyList"
          :key="item.filename"
          class="report-card"
          @click="viewReport(item)"
        >
          <div class="card-header">
            <div class="card-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
            </div>
            <button
              class="delete-btn"
              @click.stop="deleteReport(item)"
              title="Delete report"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="3 6 5 6 21 6"/>
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
              </svg>
            </button>
          </div>

          <div class="card-content">
            <h3 class="report-title">{{ item.title }}</h3>
            <p class="report-query">{{ item.query }}</p>
          </div>

          <div class="card-footer">
            <div class="footer-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              <span>{{ item.created_at }}</span>
            </div>
            <div class="footer-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" y1="15" x2="12" y2="3"/>
              </svg>
              <span>{{ formatSize(item.size) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- WeChat Modal -->
    <teleport to="body">
      <div v-if="showWechatModal" class="modal-overlay" @click.self="showWechatModal = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Publish to WeChat</h3>
            <button class="close-btn" @click="showWechatModal = false">×</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Theme Style</label>
              <select v-model="wechatTheme" class="form-select">
                <option value="tech">Tech (Blue Gradient)</option>
                <option value="minimal">Minimal (Monochrome)</option>
                <option value="business">Business (Dark Blue & Gold)</option>
              </select>
            </div>
            <div class="form-group">
              <label>Author</label>
              <input v-model="wechatAuthor" type="text" class="form-input" placeholder="Paper Agent" />
            </div>
            <div class="form-info">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="16" x2="12" y2="12"/>
                <line x1="12" y1="8" x2="12.01" y2="8"/>
              </svg>
              <p>The converted HTML will be saved to <code>output/wechat/</code></p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="showWechatModal = false">Cancel</button>
            <button class="btn-primary" @click="convertToWechat" :disabled="isConverting">
              {{ isConverting ? 'Converting...' : 'Convert to HTML' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- HTML Preview Modal -->
    <teleport to="body">
      <div v-if="showHtmlPreview" class="modal-overlay" @click.self="closeHtmlPreview">
        <div class="modal-content large">
          <div class="modal-header">
            <h3>HTML Preview</h3>
            <button class="close-btn" @click="closeHtmlPreview">×</button>
          </div>
          <div class="modal-body">
            <div class="preview-actions">
              <button class="action-btn" @click="copyHtmlContent">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                </svg>
                Copy HTML
              </button>
            </div>
            <div class="html-preview" v-html="previewHtmlContent"></div>
          </div>
          <div class="modal-footer">
            <button class="btn-secondary" @click="closeHtmlPreview">Close</button>
            <button class="btn-primary" @click="publishToWechat" :disabled="isPublishing">
              {{ isPublishing ? 'Publishing...' : 'Publish to WeChat' }}
            </button>
          </div>
        </div>
      </div>
    </teleport>
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

// WeChat modal
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
    if (!res.ok) throw new Error('Failed to load')
    historyList.value = await res.json()
  } catch (error) {
    console.error('Failed to load history:', error)
    historyList.value = []
  } finally {
    isLoading.value = false
  }
}

const viewReport = async (item) => {
  isLoading.value = true
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(item.filename)}`)
    if (!res.ok) throw new Error('Failed to load report')
    selectedReport.value = await res.json()
    editContent.value = selectedReport.value.content
    isEditing.value = false
    isModified.value = false
  } catch (error) {
    console.error('Failed to load report:', error)
    alert('Failed to load report')
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
    if (!res.ok) throw new Error('Failed to save')
    selectedReport.value.content = editContent.value
    isModified.value = false
  } catch (error) {
    console.error('Failed to save:', error)
    alert('Failed to save report')
  }
}

const copyReport = () => {
  const content = editContent.value || selectedReport.value?.content || ''
  navigator.clipboard.writeText(content)
}

const deleteReport = async (item) => {
  if (!confirm(`Delete report "${item.title}"? This cannot be undone.`)) return
  try {
    const res = await fetch(`/api/reports/${encodeURIComponent(item.filename)}`, {
      method: 'DELETE'
    })
    if (!res.ok) throw new Error('Failed to delete')
    historyList.value = historyList.value.filter(h => h.filename !== item.filename)
  } catch (error) {
    console.error('Failed to delete:', error)
    alert('Failed to delete report')
  }
}

const closeReport = () => {
  if (isModified.value && !confirm('You have unsaved changes. Discard them?')) return
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

// WeChat functions
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
    if (!res.ok) throw new Error('Conversion failed')
    const result = await res.json()
    previewHtmlContent.value = result.html_content
    currentHtmlPath.value = result.html_path
    showWechatModal.value = false
    showHtmlPreview.value = true
  } catch (error) {
    console.error('Conversion failed:', error)
    alert('Conversion failed')
  } finally {
    isConverting.value = false
  }
}

const closeHtmlPreview = () => {
  showHtmlPreview.value = false
}

const copyHtmlContent = () => {
  navigator.clipboard.writeText(previewHtmlContent.value)
}

const publishToWechat = async () => {
  if (!selectedReport.value || !previewHtmlContent.value) return
  isPublishing.value = true
  try {
    const res = await fetch('/api/wechat/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: selectedReport.value.title,
        html_content: previewHtmlContent.value,
        author: wechatAuthor.value,
        digest: selectedReport.value.query
      })
    })
    if (!res.ok) throw new Error('Publish failed')
    const result = await res.json()
    alert('Published to WeChat successfully!')
    closeHtmlPreview()
  } catch (error) {
    console.error('Publish failed:', error)
    alert('Failed to publish to WeChat: ' + error.message)
  } finally {
    isPublishing.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-studio {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeInUp var(--transition-slow);
}

/* Header */
.studio-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-8);
}

.page-title {
  font-family: var(--font-display);
  font-size: var(--text-4xl);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.title-accent {
  color: var(--color-accent-primary);
}

.page-subtitle {
  font-size: var(--text-lg);
  color: var(--color-text-secondary);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.refresh-btn:hover:not(:disabled) {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.refresh-btn svg.spinning {
  animation: spin 1s linear infinite;
}

/* Content Wrapper */
.content-wrapper {
  min-height: 500px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-20);
  color: var(--color-text-muted);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-bg-elevated);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-20);
  text-align: center;
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
}

.empty-icon svg {
  width: 40px;
  height: 40px;
}

.empty-state h3 {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-state p {
  color: var(--color-text-muted);
  margin-bottom: var(--space-6);
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  border: none;
  border-radius: var(--radius-lg);
  color: var(--color-bg-primary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.primary-btn svg {
  width: 18px;
  height: 18px);
}

/* Reports Grid */
.reports-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-5);
}

.report-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.report-card:hover {
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-glow);
  border-radius: var(--radius-lg);
  color: var(--color-accent-primary);
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.delete-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  opacity: 0;
}

.report-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--color-error-bg);
  border-color: var(--color-error);
  color: var(--color-error);
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.card-content {
  margin-bottom: var(--space-4);
}

.report-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.report-query {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  gap: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.footer-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.footer-item svg {
  width: 14px;
  height: 14px;
}

/* Detail View */
.detail-view {
  animation: fadeInUp var(--transition-base);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.back-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.back-btn svg {
  width: 16px;
  height: 16px;
}

.detail-actions {
  display: flex;
  gap: var(--space-3);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.action-btn.active {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.action-btn.primary {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.action-btn.primary:hover {
  background: var(--color-accent-hover);
}

.action-btn.wechat {
  background: var(--color-success-bg);
  border-color: var(--color-success);
  color: var(--color-success);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  padding: var(--space-4);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.meta-item svg {
  width: 16px;
  height: 16px;
  color: var(--color-accent-primary);
}

.meta-item.query {
  flex: 1;
}

.modified-badge {
  padding: var(--space-1) var(--space-3);
  background: var(--color-warning-bg);
  border: 1px solid var(--color-warning);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  color: var(--color-warning);
}

.detail-content {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.content-editor {
  width: 100%;
  min-height: 600px;
  padding: var(--space-6);
  background: var(--color-bg-secondary);
  border: none;
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  resize: vertical;
}

.content-editor:focus {
  outline: none;
}

.content-preview {
  padding: var(--space-6);
  min-height: 600px;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 10, 15, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fadeIn var(--transition-fast);
  padding: var(--space-4);
}

.modal-content {
  width: 100%;
  max-width: 500px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  animation: fadeInUp var(--transition-base);
}

.modal-content.large {
  max-width: 900px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.modal-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.modal-body {
  padding: var(--space-5);
  overflow-y: auto;
}

.form-group {
  margin-bottom: var(--space-5);
}

.form-group label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.form-select,
.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-size: var(--text-base);
  transition: all var(--transition-fast);
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.form-info {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.form-info svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: var(--color-accent-primary);
}

.form-info code {
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-primary);
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-5);
  border-top: 1px solid var(--color-border);
}

.btn-secondary,
.btn-primary {
  padding: var(--space-3) var(--space-5);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-secondary {
  background: var(--color-bg-elevated);
  color: var(--color-text-secondary);
}

.btn-secondary:hover {
  color: var(--color-text-primary);
}

.btn-primary {
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  color: var(--color-bg-primary);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Preview Modal */
.preview-actions {
  margin-bottom: var(--space-4);
}

.html-preview {
  max-height: 500px;
  overflow-y: auto;
  padding: var(--space-4);
  background: var(--color-bg-primary);
  border-radius: var(--radius-lg);
}

/* Responsive */
@media (max-width: 1024px) {
  .reports-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .studio-header {
    flex-direction: column;
    gap: var(--space-4);
  }

  .reports-grid {
    grid-template-columns: 1fr;
  }

  .detail-header {
    flex-direction: column;
    gap: var(--space-4);
  }

  .detail-meta {
    flex-direction: column;
    align-items: flex-start;
  }

  .meta-item.query {
    width: 100%;
  }
}
</style>
