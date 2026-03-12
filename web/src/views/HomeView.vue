<template>
  <div class="research-studio">
    <!-- Header -->
    <header class="studio-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-accent">New</span> Research
        </h1>
        <p class="page-subtitle">Enter your research topic and let AI do the exploration</p>
      </div>
    </header>

    <!-- Query Input Section -->
    <section class="query-section" :class="{ 'has-content': steps.length > 0 }">
      <div class="query-card">
        <div class="query-header">
          <div class="query-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"/>
              <path d="M21 21l-4.35-4.35"/>
            </svg>
          </div>
          <span class="query-label">Research Query</span>
        </div>

        <textarea
          v-model="userInput"
          class="query-input"
          placeholder="Enter your research topic or question..."
          :disabled="isSubmitting"
          @keydown.ctrl.enter="submitRequest"
          rows="4"
        ></textarea>

        <!-- Search Configuration -->
        <div class="query-config">
          <div class="config-item">
            <span class="config-label">Max Papers</span>
            <div class="config-control">
              <input
                v-model.number="maxPapers"
                type="number"
                min="1"
                max="50"
                :disabled="isSubmitting"
                class="config-input"
              />
              <input
                v-model.number="maxPapers"
                type="range"
                min="1"
                max="50"
                :disabled="isSubmitting"
                class="config-slider"
              />
              <span class="config-value">{{ maxPapers }}</span>
            </div>
          </div>
        </div>

        <div class="query-footer">
          <button
            class="knowledge-btn"
            :class="{ 'has-db': selectedDatabase }"
            @click="showSelectModal = true"
          >
            <svg v-if="selectedDatabase" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            <span>{{ selectedDatabase ? selectedDatabase.name : 'Select Knowledge Base' }}</span>
          </button>

          <button
            class="submit-btn"
            @click="submitRequest"
            :disabled="isSubmitting || !userInput.trim()"
          >
            <span v-if="isSubmitting" class="btn-loading">
              <span class="spinner"></span>
              Researching...
            </span>
            <span v-else class="btn-content">
              <span>Start Research</span>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </span>
          </button>
        </div>
      </div>
    </section>

    <!-- Research Progress -->
    <section v-if="steps.length > 0" class="progress-section">
      <div class="progress-header">
        <h2 class="section-title">Research Progress</h2>
        <div class="progress-stats">
          <span class="stat-item">{{ completedSteps }}/{{ totalSteps }} Steps</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="steps-timeline">
        <div
          v-for="(step, index) in trackSteps"
          :key="step.id"
          class="timeline-item"
          :class="step.status"
        >
          <div class="timeline-marker">
            <span v-if="step.status === 'completed'">✓</span>
            <span v-else-if="step.status === 'active'" class="marker-pulse"></span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div class="timeline-content">
            <span class="step-name">{{ step.name }}</span>
            <span v-if="step.time" class="step-time">{{ step.time }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Research Steps -->
    <section v-if="steps.length > 0" class="steps-section">
      <div class="steps-grid">
        <div
          v-for="(step, index) in steps"
          :key="index"
          class="step-card"
          :class="{
            'expanded': expandedSteps.includes(index),
            'processing': step.isProcessing,
            'error': step.isError
          }"
        >
          <div class="step-card-header" @click="toggleStep(index)">
            <div class="step-info">
              <span class="step-number">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="step-title-group">
                <h3 class="step-title">{{ step.title }}</h3>
                <span v-if="step.summary" class="step-summary">{{ step.summary }}</span>
              </div>
              <div class="step-progress-bar" v-if="step.progress > 0">
                <div class="step-progress-fill" :style="{ width: step.progress + '%' }"></div>
              </div>
            </div>
            <div class="step-actions">
              <span class="step-timestamp">{{ formatTime(step.timestamp) }}</span>
              <button class="expand-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'rotated': expandedSteps.includes(index) }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </button>
            </div>
          </div>

          <transition name="expand">
            <div v-show="expandedSteps.includes(index)" class="step-card-body">
              <div v-if="step.thinking" class="content-block">
                <div class="block-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
                  </svg>
                  Reasoning
                </div>
                <div class="thinking-content">{{ step.thinking }}</div>
              </div>

              <div v-if="step.detail" class="content-block">
                <div class="block-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                  </svg>
                  Details
                </div>
                <div class="output-content markdown-body" v-html="parseMarkdown(step.detail)"></div>
              </div>

              <!-- 流式内容显示 -->
              <div v-if="step.streamContent" class="content-block stream-block">
                <div class="block-label">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="4 17 10 11 4 5"/>
                    <line x1="12" y1="19" x2="20" y2="19"/>
                  </svg>
                  Live Output
                  <span v-if="step.isProcessing" class="live-indicator">
                    <span class="pulse"></span>
                    Writing...
                  </span>
                </div>
                <div class="stream-content markdown-body" v-html="parseMarkdown(step.streamContent)"></div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </section>

    <!-- Final Report -->
    <section v-if="reportContent" class="report-section">
      <div class="report-card">
        <div class="report-header">
          <div class="report-title">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <h2>Research Report</h2>
          </div>
          <div class="report-actions">
            <button class="action-btn" :class="{ active: reportEditing }" @click="reportEditing = !reportEditing">
              {{ reportEditing ? 'Preview' : 'Edit' }}
            </button>
            <button class="action-btn primary" @click="copyReport">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
              </svg>
              Copy
            </button>
          </div>
        </div>
        <div class="report-body">
          <textarea v-if="reportEditing" v-model="reportContent" class="report-editor"></textarea>
          <div v-else class="report-preview markdown-body" v-html="parseMarkdown(reportContent)"></div>
        </div>
      </div>
    </section>

    <!-- Review Modal -->
    <teleport to="body">
      <div v-if="isReviewing" class="modal-overlay" @click.self="isReviewing = false">
        <div class="modal-content">
          <div class="modal-header">
            <h3>Human Review Required</h3>
            <button class="close-btn" @click="isReviewing = false">×</button>
          </div>
          <div class="modal-body">
            <p class="modal-hint">The AI requires your input to proceed. Please review and provide feedback.</p>
            <textarea v-model="userReviewInput" class="review-input" rows="6" placeholder="Enter your review..."></textarea>
            <button class="submit-btn full" @click="submitReviewInput">Submit Review</button>
          </div>
        </div>
      </div>
    </teleport>

    <!-- Database Select Modal -->
    <teleport to="body">
      <SelectKnowledgeModal
        v-if="showSelectModal"
        :visible="showSelectModal"
        :current-database-id="selectedDatabase?.id || ''"
        @select="handleSelectDatabase"
        @create-database="handleCreateDatabase"
        @close="showSelectModal = false"
      />
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import SelectKnowledgeModal from '../components/SelectKnowledgeModal.vue'

const router = useRouter()

// State
const userInput = ref('')
const userReviewInput = ref('')
const isSubmitting = ref(false)
const isReviewing = ref(false)
const steps = ref([])
const expandedSteps = ref([0])
const reportContent = ref('')
const reportEditing = ref(false)
const showSelectModal = ref(false)
const selectedDatabase = ref(null)
const eventSource = ref(null)
const stepElements = ref([])
const maxPapers = ref(10)

// Track steps
const trackSteps = ref([
  { id: 'search', name: 'Literature Search', status: 'pending', time: '' },
  { id: 'reading', name: 'Paper Reading', status: 'pending', time: '' },
  { id: 'analyzing', name: 'Analysis', status: 'pending', time: '' },
  { id: 'writing', name: 'Report Writing', status: 'pending', time: '' },
  { id: 'reporting', name: 'Final Report', status: 'pending', time: '' }
])

const totalSteps = 5
const completedSteps = computed(() => trackSteps.value.filter(s => s.status === 'completed').length)
const progressPercentage = computed(() => (completedSteps.value / totalSteps) * 100)

// Methods
const parseMarkdown = (content) => {
  if (!content) return ''
  return DOMPurify.sanitize(marked.parse(content))
}

const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const toggleStep = (index) => {
  const idx = expandedSteps.value.indexOf(index)
  if (idx > -1) {
    expandedSteps.value.splice(idx, 1)
  } else {
    expandedSteps.value.push(index)
  }
}

const updateTrackStatus = (step, status, time = '') => {
  const trackStep = trackSteps.value.find(s => s.id === step)
  if (trackStep) {
    trackStep.status = status
    trackStep.time = time
  }
}

const submitRequest = () => {
  if (!userInput.value.trim()) return

  isSubmitting.value = true
  steps.value = []
  reportContent.value = ''
  expandedSteps.value = [0]
  trackSteps.value.forEach(s => { s.status = 'pending'; s.time = '' })

  eventSource.value = new EventSource(`/api/research?query=${encodeURIComponent(userInput.value)}&max_papers=${maxPapers.value}`)

  eventSource.value.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleBackendData(data)
    } catch (error) {
      console.error('Error processing event:', error)
    }
  }

  eventSource.value.onerror = () => {
    finishProcessing()
  }
}

const handleBackendData = (data) => {
  const { step, state, data: content, summary, detail, progress, stream_content } = data

  // 处理流式内容
  if (stream_content) {
    handleStreamContent(step, stream_content)
    return
  }

  switch (state) {
    case 'initializing':
      handleInitializing(step, summary, detail, progress)
      break
    case 'thinking':
      handleThinking(step, summary, detail, progress)
      break
    case 'generating':
      handleGenerating(step, summary, detail, progress)
      break
    case 'user_review':
      handleUserReview(step, detail || content)
      break
    case 'completed':
      handleComplete(step, summary, detail, progress)
      break
    case 'error':
      handleError(step, summary, detail)
      break
    case 'finished':
      handleFinish()
      break
  }
}

const handleInitializing = (step, summary, detail, progress) => {
  const stepNames = {
    searching: 'Literature Search',
    reading: 'Paper Reading',
    analyzing: 'Data Analysis',
    writing: 'Report Writing',
    reporting: 'Final Report'
  }

  // 检查是否已存在该步骤
  const existingIndex = steps.value.findIndex(s => s.step === step)
  if (existingIndex >= 0) {
    // 更新现有步骤
    steps.value[existingIndex] = {
      ...steps.value[existingIndex],
      summary,
      detail,
      progress,
      isProcessing: true
    }
    return
  }

  steps.value.push({
    step,
    title: stepNames[step] || step,
    summary,
    detail,
    progress,
    thinking: '',
    content: '',
    isProcessing: false,
    isError: false,
    timestamp: new Date().toISOString()
  })

  updateTrackStatus(step, 'active')

  nextTick(() => {
    const newIndex = steps.value.length - 1
    if (!expandedSteps.value.includes(newIndex)) {
      expandedSteps.value.push(newIndex)
    }
  })
}

const handleThinking = (step, summary, detail, progress) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = true
    currentStep.summary = summary || currentStep.summary
    currentStep.detail = detail || currentStep.detail
    if (progress) currentStep.progress = progress
    if (detail) currentStep.thinking += detail + '\n'
  }
}

const handleGenerating = (step, summary, detail, progress) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = true
    currentStep.summary = summary || currentStep.summary
    currentStep.detail = detail || currentStep.detail
    if (progress) currentStep.progress = progress
    if (detail) currentStep.content += detail + '\n'
  }
}

const handleStreamContent = (step, streamContent) => {
  // 查找或创建步骤
  let currentStep = steps.value.find(s => s.step === step)

  if (!currentStep) {
    // 如果是新的章节写作步骤，创建新步骤
    const stepNames = {
      searching: 'Literature Search',
      reading: 'Paper Reading',
      analyzing: 'Data Analysis',
      writing: 'Report Writing',
      reporting: 'Final Report'
    }

    currentStep = {
      step,
      title: stepNames[step] || step,
      summary: 'Writing in progress...',
      detail: '',
      progress: 0,
      thinking: '',
      content: '',
      streamContent: '',  // 存储流式内容
      isProcessing: true,
      isError: false,
      timestamp: new Date().toISOString()
    }
    steps.value.push(currentStep)

    // 自动展开新步骤
    nextTick(() => {
      const newIndex = steps.value.length - 1
      if (!expandedSteps.value.includes(newIndex)) {
        expandedSteps.value.push(newIndex)
      }
    })
  }

  // 追加流式内容
  if (streamContent) {
    currentStep.streamContent = (currentStep.streamContent || '') + streamContent
    currentStep.isProcessing = true
  }
}

const handleUserReview = (step, data) => {
  userReviewInput.value = data || ''
  isReviewing.value = true
}

const handleComplete = (step, summary, detail, progress) => {
  const currentStep = steps.value.find(s => s.step === step && !s.isError)
  if (currentStep) {
    currentStep.isProcessing = false
    currentStep.summary = summary || currentStep.summary
    currentStep.detail = detail || currentStep.detail
    currentStep.progress = progress || 100
    updateTrackStatus(step, 'completed', formatTime(new Date().toISOString()))
  }

  if (step === 'reporting' && detail) {
    reportContent.value = detail
  }
}

const handleError = (step, summary, detail) => {
  const currentStep = steps.value.find(s => s.step === step)
  if (currentStep) {
    currentStep.isProcessing = false
    currentStep.isError = true
    currentStep.summary = summary || 'Error'
    currentStep.detail = detail || 'An error occurred'
    currentStep.progress = 100
  }
}

const handleFinish = () => {
  finishProcessing()
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

const handleSelectDatabase = async (database) => {
  selectedDatabase.value = database
  showSelectModal.value = false
}

const handleCreateDatabase = () => {
  router.push('/knowledge')
}

onBeforeUnmount(() => {
  if (eventSource.value) {
    eventSource.value.close()
  }
})
</script>

<style scoped>
.research-studio {
  max-width: 1200px;
  margin: 0 auto;
  animation: fadeInUp var(--transition-slow);
}

/* Header */
.studio-header {
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

/* Query Section */
.query-section {
  margin-bottom: var(--space-8);
}

.query-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  transition: all var(--transition-base);
}

.query-card:hover {
  border-color: var(--color-border-hover);
}

.query-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.query-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-glow);
  border-radius: var(--radius-lg);
  color: var(--color-accent-primary);
}

.query-icon svg {
  width: 20px;
  height: 20px;
}

.query-label {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.query-input {
  width: 100%;
  min-height: 120px;
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.6;
  resize: vertical;
  transition: all var(--transition-fast);
}

.query-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px var(--color-accent-glow);
}

.query-input::placeholder {
  color: var(--color-text-muted);
}

.query-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.query-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

/* Query Configuration */
.query-config {
  display: flex;
  gap: var(--space-6);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.config-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.config-label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.config-control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.config-input {
  width: 50px;
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-primary);
  font-size: var(--text-sm);
  text-align: center;
}

.config-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.config-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-slider {
  width: 100px;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-full);
  outline: none;
}

.config-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--color-accent-primary);
  border-radius: 50%;
  cursor: pointer;
  transition: transform var(--transition-fast);
}

.config-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.config-slider:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-slider:disabled::-webkit-slider-thumb {
  cursor: not-allowed;
}

.config-value {
  min-width: 24px;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-accent-primary);
  text-align: center;
}

.knowledge-btn {
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

.knowledge-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.knowledge-btn.has-db {
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.knowledge-btn svg {
  width: 16px;
  height: 16px;
}

.submit-btn {
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

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-content {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.btn-content svg {
  width: 16px;
  height: 16px;
  transition: transform var(--transition-fast);
}

.submit-btn:hover .btn-content svg {
  transform: translateX(3px);
}

.btn-loading {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(10, 10, 15, 0.3);
  border-top-color: var(--color-bg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Progress Section */
.progress-section {
  margin-bottom: var(--space-8);
  padding: var(--space-6);
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.section-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.progress-stats {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.stat-item {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.progress-bar {
  width: 120px;
  height: 4px;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent-primary), var(--color-accent-secondary));
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

.steps-timeline {
  display: flex;
  gap: var(--space-4);
}

.timeline-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  text-align: center;
}

.timeline-marker {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 2px solid var(--color-border);
  border-radius: 50%;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  transition: all var(--transition-base);
}

.timeline-item.completed .timeline-marker {
  background: var(--color-success-bg);
  border-color: var(--color-success);
  color: var(--color-success);
}

.timeline-item.active .timeline-marker {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.marker-pulse {
  width: 12px;
  height: 12px;
  background: var(--color-accent-primary);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

.timeline-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.step-name {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.step-time {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

/* Steps Section */
.steps-section {
  margin-bottom: var(--space-8);
}

.steps-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.step-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all var(--transition-fast);
}

.step-card:hover {
  border-color: var(--color-border-hover);
}

.step-card.processing {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 1px var(--color-accent-primary);
}

.step-card.error {
  border-color: var(--color-error);
}

.step-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  cursor: pointer;
}

.step-info {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.step-number {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
}

.step-title-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.step-summary {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  font-weight: 400;
}

.step-progress-bar {
  width: 100px;
  height: 4px;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-2);
}

.step-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-accent-primary), var(--color-accent-secondary));
  border-radius: var(--radius-full);
  transition: width var(--transition-base);
}

.step-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

.step-status {
  font-size: var(--text-sm);
  color: var(--color-accent-primary);
}

.step-status.spinning {
  animation: spin 2s linear infinite;
}

.step-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.step-timestamp {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.expand-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.expand-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.expand-btn svg {
  width: 16px;
  height: 16px;
  transition: transform var(--transition-fast);
}

.expand-btn svg.rotated {
  transform: rotate(180deg);
}

.step-card-body {
  padding: 0 var(--space-5) var(--space-5);
  border-top: 1px solid var(--color-border);
  animation: fadeIn var(--transition-fast);
}

.content-block {
  margin-top: var(--space-5);
}

.block-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.block-label svg {
  width: 14px;
  height: 14px;
}

.thinking-content {
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;
  white-space: pre-wrap;
}

.output-content {
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
}

/* Report Section */
.report-section {
  margin-bottom: var(--space-8);
}

.report-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.report-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.report-title svg {
  width: 24px;
  height: 24px;
  color: var(--color-accent-primary);
}

.report-title h2 {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.report-actions {
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

.action-btn svg {
  width: 16px;
  height: 16px;
}

.report-body {
  padding: var(--space-5);
}

.report-editor {
  width: 100%;
  min-height: 400px;
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: 1.7;
  resize: vertical;
}

.report-editor:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.report-preview {
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
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
}

.modal-content {
  width: 90%;
  max-width: 500px;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  animation: fadeInUp var(--transition-base);
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
  font-size: var(--text-lg);
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
}

.modal-hint {
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.review-input {
  width: 100%;
  min-height: 120px;
  padding: var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: var(--text-base);
  resize: vertical;
  margin-bottom: var(--space-4);
}

.review-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.submit-btn.full {
  width: 100%;
  justify-content: center;
}

/* Stream Content Styles */
.stream-block {
  border: 1px solid var(--color-accent-primary);
  border-radius: var(--radius-lg);
  background: var(--color-accent-glow);
}

.stream-block .block-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-accent-primary);
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-left: auto;
  font-size: var(--text-xs);
  color: var(--color-accent-primary);
}

.pulse {
  width: 8px;
  height: 8px;
  background: var(--color-accent-primary);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.8);
  }
}

.stream-content {
  max-height: 400px;
  overflow-y: auto;
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: 1.7;
}

/* Expand Animation */
.expand-enter-active,
.expand-leave-active {
  transition: all var(--transition-base);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

/* Responsive */
@media (max-width: 1024px) {
  .steps-timeline {
    flex-wrap: wrap;
  }

  .timeline-item {
    flex: 1 1 calc(33.333% - var(--space-4));
  }
}

@media (max-width: 768px) {
  .query-footer {
    flex-direction: column;
    gap: var(--space-4);
  }

  .submit-btn {
    width: 100%;
    justify-content: center;
  }

  .progress-header {
    flex-direction: column;
    gap: var(--space-4);
    align-items: flex-start;
  }

  .steps-timeline {
    flex-direction: column;
  }

  .timeline-item {
    flex-direction: row;
    align-items: center;
    text-align: left;
  }

  .report-header {
    flex-direction: column;
    gap: var(--space-4);
  }
}
</style>
