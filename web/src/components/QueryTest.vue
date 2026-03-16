<template>
  <div class="query-test-container">
    <div class="query-input-section">
      <textarea
        v-model="queryText"
        :placeholder="selectedDatabaseId ? 'Enter your question...' : 'Select a knowledge base first'"
        rows="3"
        :disabled="!selectedDatabaseId || isQuerying"
        @keydown.ctrl.enter="handleQuery"
      ></textarea>
      <button
        class="btn-query"
        @click="handleQuery"
        :disabled="!selectedDatabaseId || !queryText.trim() || isQuerying"
      >
        <span v-if="isQuerying" class="spinner"></span>
        {{ isQuerying ? 'Querying...' : 'Query' }}
      </button>
    </div>

    <div class="query-results" v-if="queryResults.length > 0 || queryError">
      <div v-if="queryError" class="error-message">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        {{ queryError }}
      </div>

      <div v-else class="results-list">
        <div
          v-for="(result, index) in queryResults"
          :key="index"
          class="result-item"
        >
          <div class="result-header">
            <span class="result-index">#{{ index + 1 }}</span>
            <span class="result-score">Similarity: {{ formatScore(result.score) }}</span>
          </div>
          <div class="result-content">
            {{ result.content }}
          </div>
          <div class="result-meta" v-if="result.metadata && Object.keys(result.metadata).length > 0">
            <div
              v-for="(value, key) in result.metadata"
              :key="key"
              class="meta-item"
            >
              <span class="meta-label">{{ key }}:</span>
              <span class="meta-value">{{ value }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else-if="hasQueried && !isQuerying">
      <div class="empty-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
        </svg>
      </div>
      <p>No results found</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { knowledgeApi } from '../api/knowledge'

const props = defineProps({
  selectedDatabaseId: {
    type: String,
    default: ''
  }
})

const queryText = ref('')
const isQuerying = ref(false)
const queryResults = ref([])
const queryError = ref('')
const hasQueried = ref(false)

const handleQuery = async () => {
  if (!props.selectedDatabaseId || !queryText.value.trim()) {
    return
  }

  isQuerying.value = true
  queryError.value = ''
  queryResults.value = []

  try {
    const response = await knowledgeApi.queryDatabase(
      props.selectedDatabaseId,
      queryText.value,
      {}
    )

    if (response.data.status === 'success') {
      queryResults.value = response.data.result || []
    } else {
      queryError.value = response.data.message || 'Query failed'
    }
  } catch (error) {
    console.error('Query failed:', error)
    queryError.value = error.response?.data?.detail || error.message || 'Query failed, please try again'
  } finally {
    isQuerying.value = false
    hasQueried.value = true
  }
}

const formatScore = (score) => {
  if (typeof score === 'number') {
    return (score * 100).toFixed(2) + '%'
  }
  return score
}

defineExpose({
  clearResults: () => {
    queryResults.value = []
    queryError.value = ''
    hasQueried.value = false
  }
})
</script>

<style scoped>
.query-test-container {
  width: 100%;
}

.query-input-section {
  margin-bottom: var(--space-5);
}

.query-input-section textarea {
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-family: inherit;
  resize: vertical;
  margin-bottom: var(--space-3);
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.query-input-section textarea:focus {
  outline: none;
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px rgba(212, 165, 116, 0.1);
}

.query-input-section textarea:disabled {
  background: var(--color-bg-elevated);
  cursor: not-allowed;
  opacity: 0.6;
}

.query-input-section textarea::placeholder {
  color: var(--color-text-muted);
}

.btn-query {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  color: var(--color-bg-primary);
  border: none;
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-query:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-query:disabled {
  background: var(--color-bg-elevated);
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.query-results {
  max-height: 400px;
  overflow-y: auto;
}

.error-message {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-error-bg);
  color: var(--color-error);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
}

.error-message svg {
  width: 18px;
  height: 18px);
  flex-shrink: 0;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.result-item {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  transition: border-color var(--transition-fast);
}

.result-item:hover {
  border-color: var(--color-border-hover);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.result-index {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-accent-primary);
}

.result-score {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  background: var(--color-bg-elevated);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
}

.result-content {
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
  white-space: pre-wrap;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
}

.meta-item {
  font-size: var(--text-xs);
  display: flex;
  align-items: center;
  gap: var(--space-1);
  background: var(--color-bg-elevated);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
}

.meta-label {
  color: var(--color-text-muted);
}

.meta-value {
  color: var(--color-text-secondary);
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: var(--space-8) var(--space-4);
  color: var(--color-text-muted);
}

.empty-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto var(--space-3);
  color: var(--color-text-muted);
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state p {
  margin: 0;
  font-size: var(--text-sm);
}

/* Scrollbar styling */
.query-results::-webkit-scrollbar {
  width: 6px;
}

.query-results::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
}

.query-results::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-md);
}

.query-results::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted);
}
</style>
