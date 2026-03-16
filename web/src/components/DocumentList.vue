<template>
  <div class="document-list-container">
    <div class="list-header">
      <h4 class="list-title">Documents</h4>
      <span class="list-count">{{ documents.length }} files</span>
    </div>

    <div v-if="isLoading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading documents...</span>
    </div>

    <div v-else-if="documents.length === 0" class="empty-state">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <p>No documents in this knowledge base</p>
    </div>

    <div v-else class="document-list">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="document-item"
      >
        <div class="document-icon">
          <svg v-if="getFileType(doc.name) === 'pdf'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <path d="M9 15v-2a2 2 0 012-2h2"/>
          </svg>
          <svg v-else-if="getFileType(doc.name) === 'docx'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
            <polyline points="10 9 9 9 8 9"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
          </svg>
        </div>

        <div class="document-info">
          <span class="document-name" :title="doc.filename || doc.name">{{ doc.filename || doc.name || 'Unnamed' }}</span>
          <span class="document-meta">
            {{ doc.type || 'unknown' }} • {{ formatDate(doc.created_at) }}
          </span>
        </div>

        <button
          class="delete-btn"
          @click="handleDelete(doc)"
          :disabled="isDeleting === doc.id"
          title="Delete document"
        >
          <span v-if="isDeleting === doc.id" class="spinner-small"></span>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { knowledgeApi } from '../api/knowledge'

const props = defineProps({
  databaseId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['delete', 'error'])

const documents = ref([])
const isLoading = ref(false)
const isDeleting = ref('')

// Load documents on mount and when databaseId changes
onMounted(() => {
  if (props.databaseId) {
    loadDocuments()
  }
})

watch(() => props.databaseId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadDocuments()
  } else if (!newId) {
    documents.value = []
  }
})

const loadDocuments = async () => {
  if (!props.databaseId) return

  isLoading.value = true
  try {
    // Get database info which includes files
    const response = await knowledgeApi.getDatabaseInfo(props.databaseId)
    const db = response.data

    // Transform files object to array
    if (db && db.files) {
      documents.value = Object.entries(db.files).map(([id, file]) => ({
        id,
        ...file
      }))
    } else {
      documents.value = []
    }
  } catch (error) {
    console.error('Failed to load documents:', error)
    emit('error', 'Failed to load documents')
    documents.value = []
  } finally {
    isLoading.value = false
  }
}

const handleDelete = async (doc) => {
  if (!confirm(`Delete "${doc.name}"? This cannot be undone.`)) {
    return
  }

  isDeleting.value = doc.id
  try {
    await knowledgeApi.deleteDocument(props.databaseId, doc.id)
    emit('delete', doc)
    await loadDocuments() // Reload list
  } catch (error) {
    console.error('Failed to delete document:', error)
    emit('error', `Failed to delete ${doc.name}`)
  } finally {
    isDeleting.value = ''
  }
}

const getFileType = (filename) => {
  if (!filename) return 'unknown'
  const ext = filename.split('.').pop().toLowerCase()
  return ext
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

defineExpose({
  refresh: loadDocuments
})
</script>

<style scoped>
.document-list-container {
  width: 100%;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.list-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.list-count {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--color-bg-elevated);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-6);
  color: var(--color-text-muted);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.spinner-small {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  text-align: center;
  color: var(--color-text-muted);
}

.empty-icon {
  width: 40px;
  height: 40px;
  margin-bottom: var(--space-2);
  opacity: 0.5;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
}

.document-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 300px;
  overflow-y: auto;
}

.document-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.document-item:hover {
  border-color: var(--color-border-hover);
  background: var(--color-bg-elevated);
}

.document-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-glow);
  border-radius: var(--radius-md);
  color: var(--color-accent-primary);
  flex-shrink: 0;
}

.document-icon svg {
  width: 18px;
  height: 18px);
}

.document-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.document-name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.document-meta {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.delete-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.delete-btn:hover:not(:disabled) {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-btn svg {
  width: 16px;
  height: 16px);
}

/* Scrollbar styling */
.document-list::-webkit-scrollbar {
  width: 4px;
}

.document-list::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.document-list::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-md);
}

.document-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
</style>
