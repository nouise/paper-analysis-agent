<template>
  <div class="research-atelier">
    <!-- 顶部标题栏 - 极简学术风格 -->
    <header class="atelier-header">
      <div class="header-brand">
        <div class="brand-mark">PA</div>
        <h1 class="brand-title">Paper Agent</h1>
        <span class="brand-subtitle">Research Atelier</span>
      </div>
      <nav class="header-nav">
        <button class="nav-item" :class="{ active: currentView === 'research' }" @click="currentView = 'research'">
          <span class="nav-icon">◈</span>
          <span class="nav-text">Research</span>
        </button>
        <button class="nav-item" :class="{ active: currentView === 'history' }" @click="currentView = 'history'">
          <span class="nav-icon">◉</span>
          <span class="nav-text">Archive</span>
        </button>
        <button class="nav-item" :class="{ active: currentView === 'knowledge' }" @click="currentView = 'knowledge'">
          <span class="nav-icon">◆</span>
          <span class="nav-text">Library</span>
        </button>
      </nav>
    </header>

    <!-- 主内容区 -->
    <main class="atelier-main" v-if="currentView === 'research'">
      <!-- 查询输入区 - 类似学术论文搜索 -->
      <section class="query-chamber" :class="{ 'expanded': steps.length > 0 }">
        <div class="chamber-label">
          <span class="label-line"></span>
          <span class="label-text">Research Query</span>
          <span class="label-line"></span>
        </div>
        <div class="query-input-wrapper">
          <textarea
            v-model="userInput"
            class="query-textarea"
            placeholder="Enter your research inquiry..."
            :disabled="isSubmitting"
            @keydown.ctrl.enter="submitRequest"
          ></textarea>
          <div class="query-meta">
            <div class="knowledge-badge" v-if="selectedDatabase" @click="showSelectModal = true">
              <span class="badge-icon">✦</span>
              <span class="badge-text">{{ selectedDatabase.name }}</span>
            </div>
            <div class="knowledge-badge empty" v-else @click="showSelectModal = true">
              <span class="badge-icon">+</span>
              <span class="badge-text">Knowledge Base</span>
            </div>
            <button class="submit-btn" @click="submitRequest" :disabled="isSubmitting || !userInput.trim()">
              <span class="btn-text">{{ isSubmitting ? 'Researching...' : 'Begin Research' }}</span>
              <span class="btn-arrow">→</span>
            </button>
          </div>
        </div>
      </section>

      <!-- 研究流程展示区 -->
      <section class="research-workspace" v-if="steps.length > 0">
        <!-- 左侧进度轨道 -->
        <aside class="progress-track">
          <div class="track-header">
            <h3>Progress</h3>
            <span class="track-count">{{ completedSteps }}/{{ totalSteps }}</span>
          </div>
          <div class="track-line">
            <div class="track-progress" :style="{ height: progressPercentage + '%' }"></div>
          </div>
          <div class="track-steps">
            <div
              v-for="(step, index) in trackSteps"
              :key="step.id"
              class="track-step"
              :class="{
                'completed': step.status === 'completed',
                'active': step.status === 'active',
                'pending': step.status === 'pending'
              }"
              @click="scrollToStep(index)"
            >
              <div class="step-node">
                <span v-if="step.status === 'completed'">✓</span>
                <span v-else-if="step.status === 'active'" class="pulse"></span>
                <span v-else>{{ index + 1 }}</span>
              </div>
              <div class="step-info">
                <span class="step-name">{{ step.name }}</span>
                <span class="step-time" v-if="step.time">{{ step.time }}</span>
              </div>
            </div>
          </div>
        </aside>

        <!-- 主内容区 -->
        <div class="workspace-content">
          <div class="content-scroll" ref="contentScroll">
            <!-- 各个步骤卡片 -->
            <div
              v-for="(step, index) in steps"
              :key="index"
              class="step-card"
              :class="{
                'expanded': expandedSteps.includes(index),
                'processing': step.isProcessing,
                'error': step.isError
              }"
              :data-step="step.step"
              :ref="el => { if (el) stepElements[index] = el }"
            >
              <div class="card-header" @click="toggleStep(index)">
                <div class="header-left">
                  <span class="step-index">{{ String(index + 1).padStart(2, '0') }}</span>
                  <div class="step-title-group">
                    <h4 class="step-title">{{ step.title }}</h4>
                    <span class="step-status" :class="{ 'spinning': step.isProcessing }">
                      {{ step.isProcessing ? '◐' : step.isError ? '✕' : '✓' }}
                    </span>
                  </div>
                </div>
                <div class="header-right">
                  <span class="step-timestamp">{{ formatTime(step.timestamp) }}</span>
                  <button class="expand-btn">
                    {{ expandedSteps.includes(index) ? '−' : '+' }}
                  </button>
                </div>
              </div>

              <transition name="slide">
                <div class="card-body" v-show="expandedSteps.includes(index)">
                  <!-- 思考过程 -->
                  <div class="thinking-section" v-if="step.thinking">
                    <div class="section-label">Reasoning Process</div>
                    <div class="thinking-content">{{ step.thinking }}</div>
                  </div>
                  <!-- 内容 -->
                  <div class="content-section" v-if="step.content">
                    <div class="section-label">Output</div>
                    <div class="content-output markdown-body" v-html="parseMarkdown(step.content)"></div>
                  </div>
                </div>
              </transition>
            </div>

            <!-- 最终报告 -->
            <div class="final-report" v-if="reportContent" ref="finalReport">
              <div class="report-header">
                <div class="report-title-group">
                  <span class="report-icon">◈</span>
                  <h3>Research Report</h3>
                </div>
                <div class="report-actions">
                  <button class="action-btn" :class="{ active: reportEditing }" @click="reportEditing = !reportEditing">
                    {{ reportEditing ? 'Preview' : 'Edit' }}
                  </button>
                  <button class="action-btn primary" @click="copyReport">Copy</button>
                  <button class="action-btn primary" v-if="reportEditing && reportModified" @click="saveReport">Save</button>
                </div>
              </div>
              <div class="report-body">
                <textarea v-if="reportEditing" v-model="reportContent" class="report-editor"></textarea>
                <div v-else class="report-preview markdown-body" v-html="parseMarkdown(reportContent)"></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 人工审核面板 -->
      <div class="review-panel" v-if="isReviewing">
        <div class="panel-overlay" @click="isReviewing = false"></div>
        <div class="panel-content">
          <div class="panel-header">
            <h3>Human Review Required</h3>
            <button class="close-btn" @click="isReviewing = false">×</button>
          </div>
          <div class="panel-body">
            <p class="review-hint">The AI requires your input to proceed. Please review and provide feedback.</p>
            <textarea v-model="userReviewInput" class="review-input" rows="6" placeholder="Enter your review..."></textarea>
            <button class="submit-review-btn" @click="submitReviewInput">Submit Review</button>
          </div>
        </div>
      </div>
    </main>

    <!-- 历史记录视图 -->
    <main class="archive-view" v-else-if="currentView === 'history'">
      <div class="archive-header">
        <h2>Research Archive</h2>
        <p class="archive-subtitle">Previously generated research reports</p>
      </div>
      <div class="archive-grid">
        <div v-for="report in reports" :key="report.filename" class="archive-item">
          <div class="item-header">
            <span class="item-date">{{ report.created_at }}</span>
            <span class="item-size">{{ formatSize(report.size) }}</span>
          </div>
          <h4 class="item-title">{{ report.title }}</h4>
          <p class="item-query">{{ report.query }}</p>
          <div class="item-actions">
            <button class="item-btn" @click="viewReport(report)">View</button>
            <button class="item-btn" @click="downloadReport(report)">Download</button>
          </div>
        </div>
      </div>
    </main>

    <!-- 知识库视图 -->
    <main class="library-view" v-else-if="currentView === 'knowledge'">
      <div class="library-placeholder">
        <span class="placeholder-icon">◆</span>
        <h2>Knowledge Library</h2>
        <p>Manage your research knowledge bases</p>
        <button class="navigate-btn" @click="goToKnowledgeBase">Open Library</button>
      </div>
    </main>

    <!-- 知识库选择模态框 -->
    <teleport to="body">
      <div class="modal-overlay" v-if="showSelectModal" @click.self="showSelectModal = false">
        <SelectKnowledgeModal
          :visible="showSelectModal"
          :current-database-id="selectedDatabase?.id || ''"
          @select="handleSelectDatabase"
          @create-database="handleCreateDatabase"
          @close="showSelectModal = false"
        />
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, nextTick, onBeforeUnmount, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import SelectKnowledgeModal from './components/SelectKnowledgeModal.vue'
import { knowledgeApi } from './api/knowledge'

const router = useRouter()

// State
const currentView = ref('research')
const userInput = ref('')
const userReviewInput = ref('')
const isSubmitting = ref(false)
const isReviewing = ref(false)
const steps = ref([])
const expandedSteps = ref([0])
const reportContent = ref('')
const reportEditing = ref(false)
const reportModified = ref(false)
const showSelectModal = ref(false)
const selectedDatabase = ref(null)
const eventSource = ref(null)
const stepElements = ref([])
const contentScroll = ref(null)
const reports = ref([])

// Track steps for sidebar
const trackSteps = ref([
  { id: 'search', name: 'Search', status: 'pending', time: '' },
  { id: 'reading', name: 'Reading', status: 'pending', time: '' },
  { id: 'analyzing', name: 'Analysis', status: 'pending', time: '' },
  { id: 'writing', name: 'Writing', status: 'pending', time: '' },
  { id: 'reporting', name: 'Report', status: 'pending', time: '' }
])

const totalSteps = 5
const completedSteps = computed(() => trackSteps.value.filter(s => s.status === 'completed').length)
const progressPercentage = computed(() => (completedSteps.value / totalSteps) * 100)

// Parse markdown
const parseMarkdown = (content) => {
  if (!content) return ''
  const html = marked.parse(content)
  return DOMPurify.sanitize(html)
}

// Format timestamp
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Format file size
const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Toggle step expansion
const toggleStep = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx > -1) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

// Scroll to step
const scrollToStep = (index) => {
  const element = stepElements.value[index]
  if (element && contentScroll.value) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// Update track status
const updateTrackStatus = (step, status, time = '') {
  const trackStep = trackSteps.value.find(s => s.id === step)
  if (trackStep) {
    trackStep.status = status
    trackStep.time = time
  }
}

// Submit request
const submitRequest = () => {
  if (!userInput.value.trim()) return

  isSubmitting.value = true
  steps.value = []
  reportContent.value = ''
  expandedSteps.value = [0]
  trackSteps.value.forEach(s => { s.status = 'pending'; s.time = '' })

  eventSource.value = new EventSource(`/api/research?query=${encodeURIComponent(userInput.value)}`)

  eventSource.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleBackendData(data)
    } catch (error) {
      console.error('Error processing event:', error)
    }
  }

  eventSource.value.onerror = () => {
    addStep('Error', 'Connection failed', null, true)
    finishProcessing()
  }
}

// Handle backend data
const handleBackendData = (data) => {
  const { step, state, data: content } = data

  switch (state) {
    case 'initializing':
      handleInitializing(step, content)
      break
    case 'thinking':
      handleThinking(step, content)
      break
    case 'generating':
      handleGenerating(step, content)
      break
    case 'user_review':
      handleUserReview(step, content)
      break
    case 'completed':
      handleComplete(step, content)
      break
    case 'error':
      handleError(step, content)
      break
    case 'finished':
      handleFinish()
      break
  }
}

const handleInitializing = (step, data) => {
  const stepNames = {
    searching: 'Literature Search',
    reading: 'Paper Reading',
    analyzing: 'Data Analysis',
    writing: 'Report Writing',
    reporting: 'Final Report'
  }

  const stepData = {
    step,
    title: stepNames[step] || step,
    thinking: '',
    content: '',
    isProcessing: false,
    isError: false,
    timestamp: new Date().toISOString()
  }

  steps.value.push(stepData)
  updateTrackStatus(step, 'active')

  nextTick(() => {
    const newIndex = steps.value.length - 1
    if (!expandedSteps.value.includes(newIndex)) {
      expandedSteps.value.push(newIndex)
    }
  })
}

const handleThinking = (step, data) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = true
    if (data) currentStep.thinking += data
  }
}

const handleGenerating = (step, data) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = true
    if (data) currentStep.content += data
  }
}

const handleUserReview = (step, data) => {
  userReviewInput.value = data || ''
  isReviewing.value = true
}

const handleComplete = (step, data) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = false
    if (data) currentStep.content += data
    updateTrackStatus(step, 'completed', formatTime(new Date().toISOString()))
  }

  if (step === 'reporting' && data) {
    reportContent.value = data
  }
}

const handleError = (step, data) => {
  const currentStep = steps.value.find(s => s.step === step)
  if (currentStep) {
    currentStep.isProcessing = false
    currentStep.isError = true
    if (data) currentStep.content += data
  }
}

const handleFinish = () => {
  addStep('Complete', 'Research completed successfully', null, false, true)
  finishProcessing()
}

const addStep = (title, content, thinking = null, isError = false, isFinish = false) => {
  steps.value.push({
    step: isFinish ? 'finish' : 'error',
    title,
    content,
    thinking,
    isProcessing: false,
    isError,
    timestamp: new Date().toISOString()
  })
}

const finishProcessing = () => {
  isSubmitting.value = false
  if (eventSource.value) {
    eventSource.value.close()
  }
}

const submitReviewInput = async () => {
  if (!userReviewInput.value.trim()) return

  try {
    const res = await fetch('/send_input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: userReviewInput.value })
    })

    if (res.ok) {
      isReviewing.value = false
    }
  } catch (err) {
    console.error(err)
  }
}

const copyReport = () => {
  navigator.clipboard.writeText(reportContent.value)
}

const saveReport = async () => {
  // Implementation for saving report
  reportModified.value = false
}

const handleSelectDatabase = async (database) => {
  selectedDatabase.value = database
  showSelectModal.value = false
}

const handleCreateDatabase = () => {
  router.push('/knowledge')
}

const goToKnowledgeBase = () => {
  router.push('/knowledge')
}

const viewReport = (report) => {
  // Implementation for viewing report
}

const downloadReport = (report) => {
  // Implementation for downloading report
}

onBeforeUnmount(() => {
  if (eventSource.value) {
    eventSource.value.close()
  }
})

// Fetch reports on mount
const fetchReports = async () => {
  try {
    const res = await fetch('/api/reports')
    if (res.ok) {
      reports.value = await res.json()
    }
  } catch (err) {
    console.error('Failed to fetch reports:', err)
  }
}

fetchReports()
</script>

<style scoped>
/* CSS Variables - Academic Atelier Theme */
:root {
  --color-bg-primary: #0f0f1a;
  --color-bg-secondary: #16162a;
  --color-bg-tertiary: #1e1e3a;
  --color-bg-elevated: #252550;
  --color-accent-primary: #d4a574;
  --color-accent-secondary: #c49a6c;
  --color-accent-muted: #8b7355;
  --color-text-primary: #e8e6e1;
  --color-text-secondary: #a0998f;
  --color-text-muted: #6b6560;
  --color-border: rgba(212, 165, 116, 0.15);
  --color-border-hover: rgba(212, 165, 116, 0.3);
  --color-success: #7ca782;
  --color-error: #c97b7b;
  --color-processing: #6b8cae;

  --font-display: 'Playfair Display', 'Noto Serif', Georgia, serif;
  --font-body: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2.5rem;
  --spacing-2xl: 4rem;

  --radius-sm: 2px;
  --radius-md: 4px;
  --radius-lg: 8px;

  --transition-fast: 150ms ease;
  --transition-medium: 300ms ease;
  --transition-slow: 500ms ease;
}

/* Reset & Base */
.research-atelier {
  min-height: 100vh;
  background: var(--color-bg-primary);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Header */
.atelier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 1px solid var(--color-border);
  background: linear-gradient(180deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.brand-mark {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-primary);
  color: var(--color-bg-primary);
  font-family: var(--font-display);
  font-size: 1.25rem;
  font-weight: 700;
  border-radius: var(--radius-sm);
}

.brand-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-left: var(--spacing-sm);
}

.header-nav {
  display: flex;
  gap: var(--spacing-xs);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-item:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border);
}

.nav-item.active {
  color: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  background: rgba(212, 165, 116, 0.05);
}

.nav-icon {
  font-size: 0.75rem;
}

/* Main Content */
.atelier-main {
  max-width: 1400px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

/* Query Chamber */
.query-chamber {
  margin-bottom: var(--spacing-2xl);
  transition: all var(--transition-medium);
}

.query-chamber.expanded {
  margin-bottom: var(--spacing-xl);
}

.chamber-label {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.label-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-border), transparent);
}

.label-text {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--color-text-muted);
}

.query-input-wrapper {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: all var(--transition-fast);
}

.query-input-wrapper:focus-within {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.1);
}

.query-textarea {
  width: 100%;
  min-height: 120px;
  background: transparent;
  border: none;
  color: var(--color-text-primary);
  font-size: 1.125rem;
  font-family: var(--font-body);
  line-height: 1.7;
  resize: vertical;
  outline: none;
}

.query-textarea::placeholder {
  color: var(--color-text-muted);
}

.query-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.knowledge-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.knowledge-badge:hover {
  border-color: var(--color-accent-primary);
}

.knowledge-badge.empty {
  color: var(--color-text-muted);
}

.badge-icon {
  color: var(--color-accent-primary);
  font-size: 0.875rem;
}

.badge-text {
  font-size: 0.875rem;
}

.submit-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-bg-primary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-accent-secondary);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-arrow {
  transition: transform var(--transition-fast);
}

.submit-btn:hover .btn-arrow {
  transform: translateX(3px);
}

/* Research Workspace */
.research-workspace {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: var(--spacing-xl);
}

/* Progress Track */
.progress-track {
  position: sticky;
  top: var(--spacing-xl);
  height: fit-content;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.track-header h3 {
  font-family: var(--font-display);
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.track-count {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.track-line {
  position: relative;
  width: 2px;
  height: 60px;
  background: var(--color-bg-elevated);
  margin: 0 auto var(--spacing-md);
  border-radius: 1px;
}

.track-progress {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(180deg, var(--color-accent-primary), var(--color-accent-muted));
  border-radius: 1px;
  transition: height var(--transition-slow);
}

.track-steps {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.track-step {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.track-step:hover {
  background: var(--color-bg-tertiary);
}

.step-node {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 50%;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
}

.track-step.completed .step-node {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.track-step.active .step-node {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.pulse {
  width: 8px;
  height: 8px;
  background: var(--color-bg-primary);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.step-info {
  display: flex;
  flex-direction: column;
}

.step-name {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}

.track-step.completed .step-name,
.track-step.active .step-name {
  color: var(--color-text-primary);
}

.step-time {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

/* Workspace Content */
.workspace-content {
  min-height: 600px;
}

.content-scroll {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* Step Cards */
.step-card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-medium);
}

.step-card:hover {
  border-color: var(--color-border-hover);
}

.step-card.processing {
  border-color: var(--color-processing);
  box-shadow: 0 0 0 1px var(--color-processing);
}

.step-card.error {
  border-color: var(--color-error);
  box-shadow: 0 0 0 1px var(--color-error);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  cursor: pointer;
  background: linear-gradient(90deg, var(--color-bg-tertiary) 0%, transparent 100%);
  border-bottom: 1px solid var(--color-border);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.step-index {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--color-text-muted);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-sm);
}

.step-title-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.step-title {
  font-family: var(--font-display);
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.step-status {
  font-size: 0.875rem;
  color: var(--color-success);
}

.step-status.spinning {
  animation: spin 2s linear infinite;
  color: var(--color-processing);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.step-timestamp {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.expand-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-secondary);
  font-size: 1rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.card-body {
  padding: var(--spacing-lg);
}

.section-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-sm);
}

.thinking-section {
  margin-bottom: var(--spacing-lg);
}

.thinking-content {
  font-family: var(--font-mono);
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  background: var(--color-bg-tertiary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  white-space: pre-wrap;
  line-height: 1.7;
}

.content-output {
  color: var(--color-text-primary);
  line-height: 1.7;
}

/* Slide Animation */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-medium);
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* Final Report */
.final-report {
  margin-top: var(--spacing-xl);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(90deg, var(--color-accent-muted) 0%, transparent 100%);
  border-bottom: 1px solid var(--color-border);
}

.report-title-group {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.report-icon {
  color: var(--color-accent-primary);
  font-size: 1.25rem;
}

.report-header h3 {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary);
}

.report-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.action-btn {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.action-btn.primary {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.action-btn.primary:hover {
  background: var(--color-accent-secondary);
}

.action-btn.active {
  background: var(--color-bg-elevated);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.report-body {
  padding: var(--spacing-lg);
}

.report-editor {
  width: 100%;
  min-height: 500px;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-lg);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: 0.875rem;
  line-height: 1.7;
  resize: vertical;
  outline: none;
}

.report-editor:focus {
  border-color: var(--color-accent-primary);
}

.report-preview {
  line-height: 1.7;
}

/* Review Panel */
.review-panel {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.panel-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 15, 26, 0.8);
  backdrop-filter: blur(4px);
}

.panel-content {
  position: relative;
  width: 100%;
  max-width: 600px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.panel-header h3 {
  font-family: var(--font-display);
  font-size: 1.125rem;
  margin: 0;
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
  font-size: 1.5rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-btn:hover {
  border-color: var(--color-error);
  color: var(--color-error);
}

.panel-body {
  padding: var(--spacing-lg);
}

.review-hint {
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.review-input {
  width: 100%;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: 0.875rem;
  line-height: 1.7;
  resize: vertical;
  outline: none;
  margin-bottom: var(--spacing-md);
}

.review-input:focus {
  border-color: var(--color-accent-primary);
}

.submit-review-btn {
  width: 100%;
  padding: var(--spacing-md);
  background: var(--color-accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-bg-primary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.submit-review-btn:hover {
  background: var(--color-accent-secondary);
}

/* Archive View */
.archive-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--spacing-xl);
}

.archive-header {
  text-align: center;
  margin-bottom: var(--spacing-2xl);
}

.archive-header h2 {
  font-family: var(--font-display);
  font-size: 2rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm);
}

.archive-subtitle {
  color: var(--color-text-muted);
}

.archive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

.archive-item {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: all var(--transition-fast);
}

.archive-item:hover {
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
}

.item-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-sm);
}

.item-date {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.item-size {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.item-title {
  font-family: var(--font-display);
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 var(--spacing-sm);
  color: var(--color-text-primary);
}

.item-query {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-bottom: var(--spacing-md);
}

.item-actions {
  display: flex;
  gap: var(--spacing-sm);
}

.item-btn {
  flex: 1;
  padding: var(--spacing-sm);
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.item-btn:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

/* Library View */
.library-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.library-placeholder {
  text-align: center;
}

.placeholder-icon {
  font-size: 4rem;
  color: var(--color-accent-primary);
  opacity: 0.5;
}

.library-placeholder h2 {
  font-family: var(--font-display);
  font-size: 1.875rem;
  margin: var(--spacing-md) 0 var(--spacing-sm);
}

.library-placeholder p {
  color: var(--color-text-muted);
  margin-bottom: var(--spacing-lg);
}

.navigate-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  background: var(--color-accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-bg-primary);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.navigate-btn:hover {
  background: var(--color-accent-secondary);
}

/* Modal Overlay */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 15, 26, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

/* Markdown Styles */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  font-family: var(--font-display);
  color: var(--color-text-primary);
  margin-top: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.markdown-body :deep(h1) {
  font-size: 1.75rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: var(--spacing-sm);
}

.markdown-body :deep(h2) {
  font-size: 1.375rem;
}

.markdown-body :deep(h3) {
  font-size: 1.125rem;
}

.markdown-body :deep(p) {
  margin-bottom: var(--spacing-md);
  color: var(--color-text-secondary);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: var(--spacing-lg);
  margin-bottom: var(--spacing-md);
}

.markdown-body :deep(li) {
  margin-bottom: var(--spacing-xs);
  color: var(--color-text-secondary);
}

.markdown-body :deep(code) {
  font-family: var(--font-mono);
  background: var(--color-bg-tertiary);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-sm);
  font-size: 0.875rem;
}

.markdown-body :deep(pre) {
  background: var(--color-bg-tertiary);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin-bottom: var(--spacing-md);
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-body :deep(a) {
  color: var(--color-accent-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(blockquote) {
  border-left: 2px solid var(--color-accent-primary);
  padding-left: var(--spacing-md);
  margin-left: 0;
  color: var(--color-text-muted);
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: var(--spacing-md);
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: var(--spacing-sm);
  border: 1px solid var(--color-border);
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--color-bg-tertiary);
  font-weight: 600;
}

/* Responsive */
@media (max-width: 1024px) {
  .research-workspace {
    grid-template-columns: 1fr;
  }

  .progress-track {
    position: relative;
    top: 0;
    order: -1;
  }

  .track-line {
    display: none;
  }

  .track-steps {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .track-step {
    flex: 1;
    min-width: 150px;
  }
}

@media (max-width: 768px) {
  .atelier-header {
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
  }

  .header-nav {
    width: 100%;
    justify-content: center;
  }

  .atelier-main {
    padding: var(--spacing-md);
  }

  .query-meta {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .submit-btn {
    width: 100%;
    justify-content: center;
  }

  .card-header {
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .report-header {
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .report-actions {
    width: 100%;
    justify-content: stretch;
  }

  .action-btn {
    flex: 1;
  }

  .archive-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .brand-title {
    font-size: 1.25rem;
  }

  .brand-subtitle {
    display: none;
  }

  .nav-text {
    display: none;
  }

  .track-steps {
    flex-direction: column;
  }
}

/* Font Loading */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+Pro:wght@400;600&family=JetBrains+Mono&display=swap');
</style>
