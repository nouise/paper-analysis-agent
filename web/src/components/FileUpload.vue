<template>
  <div class="upload-container">
    <div
      class="upload-zone"
      :class="{ 'drag-over': isDragOver, disabled: !selectedDatabaseId }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="zone-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
      </div>
      <p class="zone-title">
        {{ selectedDatabaseId ? 'Drop files here or click to upload' : 'Select a knowledge base first' }}
      </p>
      <p v-if="selectedDatabaseId" class="zone-hint">
        Supported: {{ supportedTypes.join(', ') }}
      </p>
      <input
        ref="fileInput"
        type="file"
        multiple
        :accept="acceptTypes"
        @change="handleFileSelect"
        style="display: none"
      />
    </div>

    <!-- Upload Queue -->
    <div v-if="uploadQueue.length > 0" class="upload-queue">
      <h4 class="queue-title">Upload Queue</h4>
      <div class="queue-list">
        <div
          v-for="(file, index) in uploadQueue"
          :key="index"
          class="queue-item"
          :class="file.status"
        >
          <div class="item-info">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            <div class="item-details">
              <span class="item-name">{{ file.name }}</span>
              <span class="item-size">{{ formatFileSize(file.size) }}</span>
            </div>
          </div>
          <div class="item-status">
            <span v-if="file.status === 'uploading'" class="status-badge uploading">
              <span class="spinner"></span>
              {{ file.progress }}%
            </span>
            <span v-else-if="file.status === 'parsing'" class="status-badge parsing">
              <span class="spinner"></span>
              Parsing
            </span>
            <span v-else-if="file.status === 'success'" class="status-badge success">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span v-if="file.parsed">Parsed ({{ file.contentLength }} chars)</span>
              <span v-else>Done</span>
            </span>
            <span v-else-if="file.status === 'uploaded'" class="status-badge uploaded">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              Uploaded
            </span>
            <span v-else-if="file.status === 'failed'" class="status-badge failed">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
              Failed
            </span>
            <button
              v-if="file.status === 'uploaded'"
              class="add-btn"
              @click.stop="addToKnowledgeBase(file)"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add to KB
            </button>
            <span v-else-if="file.status === 'adding'" class="status-badge adding">
              <span class="spinner"></span>
              Adding...
            </span>
            <span v-else class="status-badge pending">Pending</span>
          </div>
        </div>
      </div>
      <button v-if="!isUploading" class="clear-btn" @click="clearQueue">
        Clear Queue
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { knowledgeApi } from '../api/knowledge'

const props = defineProps({
  selectedDatabaseId: { type: String, default: '' }
})

const emit = defineEmits(['upload-complete', 'upload-error', 'file-uploaded'])

const fileInput = ref(null)
const isDragOver = ref(false)
const uploadQueue = ref([])
const isUploading = ref(false)
const supportedTypes = ref([])

const acceptTypes = computed(() => {
  return supportedTypes.value.map(type => `.${type}`).join(',')
})

onMounted(async () => {
  await loadSupportedTypes()
})

const loadSupportedTypes = async () => {
  try {
    const response = await knowledgeApi.getSupportedTypes()
    supportedTypes.value = response.data.file_types || []
  } catch (error) {
    console.error('Failed to load supported types:', error)
    supportedTypes.value = ['pdf', 'docx', 'txt', 'md']
  }
}

const handleDragOver = () => {
  if (!props.selectedDatabaseId) return
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleDrop = (event) => {
  if (!props.selectedDatabaseId) return
  isDragOver.value = false
  const files = Array.from(event.dataTransfer.files)
  addFilesToQueue(files)
}

const triggerFileInput = () => {
  if (!props.selectedDatabaseId) return
  fileInput.value.click()
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFilesToQueue(files)
  event.target.value = ''
}

const addFilesToQueue = (files) => {
  files.forEach(file => {
    uploadQueue.value.push({
      file,
      name: file.name,
      size: file.size,
      status: 'pending',
      progress: 0,
      error: null
    })
  })
  processQueue()
}

const processQueue = async () => {
  if (isUploading.value) return
  isUploading.value = true

  for (let i = 0; i < uploadQueue.value.length; i++) {
    const item = uploadQueue.value[i]
    if (item.status === 'pending' || item.status === 'failed') {
      await uploadFile(item)
    }
  }

  isUploading.value = false
}

const uploadFile = async (item) => {
  item.status = 'uploading'
  item.progress = 0

  try {
    const response = await knowledgeApi.uploadFile(item.file, props.selectedDatabaseId)
    item.status = 'uploaded'
    item.progress = 100

    // 保存解析状态
    if (response.data.parsed) {
      item.parsed = true
      item.contentLength = response.data.content_length
      item.parserType = response.data.parser_type
    }

    // 保存文件路径，用于后续添加到知识库
    item.filePath = response.data.file_path

    emit('file-uploaded', item)
  } catch (error) {
    item.status = 'failed'
    item.error = error.response?.data?.detail || error.message || 'Upload failed'
    emit('upload-error', item)
  }
}

const clearQueue = () => {
  uploadQueue.value = []
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const addToKnowledgeBase = async (item) => {
  if (!item.filePath) {
    item.status = 'failed'
    item.error = 'No file path available'
    emit('upload-error', item)
    return
  }

  item.status = 'adding'
  try {
    await knowledgeApi.addDocuments(props.selectedDatabaseId, [item.filePath], { content_type: 'file' })
    item.status = 'success'
    emit('upload-complete', item)
  } catch (error) {
    item.status = 'failed'
    item.error = error.response?.data?.detail || error.message || 'Failed to add to knowledge base'
    emit('upload-error', item)
  }
}

defineExpose({ clearQueue })
</script>

<style scoped>
.upload-container {
  width: 100%;
}

.upload-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  background: var(--color-bg-secondary);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.upload-zone:hover:not(.disabled) {
  border-color: var(--color-border-hover);
  background: var(--color-bg-elevated);
}

.upload-zone.drag-over {
  border-color: var(--color-accent-primary);
  background: var(--color-accent-glow);
}

.upload-zone.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.zone-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted);
}

.zone-icon svg {
  width: 32px;
  height: 32px;
}

.zone-title {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.zone-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* Upload Queue */
.upload-queue {
  margin-top: var(--space-6);
}

.queue-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.queue-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.queue-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.queue-item.success {
  border-color: var(--color-success);
}

.queue-item.failed {
  border-color: var(--color-error);
}

.queue-item.uploaded {
  border-color: var(--color-accent-primary);
}

.item-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.item-info svg {
  width: 20px;
  height: 20px;
  color: var(--color-text-muted);
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.item-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
}

.item-size {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.item-status {
  display: flex;
  align-items: center;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: 500;
}

.status-badge.pending {
  background: var(--color-bg-elevated);
  color: var(--color-text-muted);
}

.status-badge.uploading {
  background: var(--color-accent-glow);
  color: var(--color-accent-primary);
}

.status-badge.parsing {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.status-badge.success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.status-badge.failed {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.status-badge.uploaded {
  background: var(--color-accent-glow);
  color: var(--color-accent-primary);
}

.status-badge.adding {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.status-badge svg {
  width: 14px;
  height: 14px;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-3);
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-bg-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.add-btn svg {
  width: 12px;
  height: 12px;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(212, 165, 116, 0.2);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.clear-btn {
  width: 100%;
  padding: var(--space-2);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-secondary);
}
</style>
