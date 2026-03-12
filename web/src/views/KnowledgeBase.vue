<template>
  <div class="library-studio">
    <!-- Header -->
    <header class="studio-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-accent">Knowledge</span> Library
        </h1>
        <p class="page-subtitle">Manage your research knowledge bases and documents</p>
      </div>
      <button class="create-btn" @click="showCreateModal = true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Create Knowledge Base
      </button>
    </header>

    <!-- Content -->
    <div class="content-wrapper">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading knowledge bases...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="databases.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <ellipse cx="12" cy="5" rx="9" ry="3"/>
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
        </div>
        <h3>No Knowledge Bases</h3>
        <p>Create your first knowledge base to get started</p>
        <button class="primary-btn" @click="showCreateModal = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          Create Knowledge Base
        </button>
      </div>

      <!-- Content Grid -->
      <div v-else class="content-grid">
        <!-- Databases List -->
        <div class="databases-panel">
          <div class="panel-header">
            <h2 class="panel-title">Knowledge Bases</h2>
            <span class="panel-count">{{ databases.length }} total</span>
          </div>

          <div class="databases-list">
            <DatabaseCard
              v-for="database in databases"
              :key="database.id"
              :database="database"
              :is-selected="selectedDatabaseId === database.id"
              @select="handleSelectDatabase"
              @delete="handleDeleteDatabase"
              @edit="handleEditDatabase"
            />
          </div>
        </div>

        <!-- Side Panel -->
        <div v-if="selectedDatabase" class="side-panel">
          <div class="panel-card">
            <div class="panel-card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
              <h3>Upload Documents</h3>
            </div>
            <FileUpload
              :selected-database-id="selectedDatabaseId"
              @upload-complete="handleUploadComplete"
              @upload-error="handleUploadError"
              @file-uploaded="handleFileUploaded"
            />
          </div>

          <div class="panel-card">
            <div class="panel-card-header">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="M21 21l-4.35-4.35"/>
              </svg>
              <h3>Test Query</h3>
            </div>
            <QueryTest
              :selected-database-id="selectedDatabaseId"
              ref="queryTestRef"
            />
          </div>
        </div>

        <!-- Empty Selection State -->
        <div v-else class="side-panel empty">
          <div class="empty-selection">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
            <h4>Select a Knowledge Base</h4>
            <p>Choose a knowledge base to upload documents or test queries</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="slide">
      <div v-if="toast.show" class="toast" :class="toast.type">
        <svg v-if="toast.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
          <polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="15" y1="9" x2="9" y2="15"/>
          <line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        {{ toast.message }}
      </div>
    </transition>

    <!-- Create Modal -->
    <CreateDatabaseModal
      v-model:visible="showCreateModal"
      @submit="handleCreateDatabase"
    />

    <!-- Edit Modal -->
    <CreateDatabaseModal
      v-model:visible="showEditModal"
      :database="editingDatabase"
      mode="edit"
      @submit="handleUpdateDatabase"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { knowledgeApi } from '../api/knowledge'
import DatabaseCard from '../components/DatabaseCard.vue'
import CreateDatabaseModal from '../components/CreateDatabaseModal.vue'
import FileUpload from '../components/FileUpload.vue'
import QueryTest from '../components/QueryTest.vue'

const databases = ref([])
const selectedDatabaseId = ref('')
const selectedDatabase = ref(null)
const isLoading = ref(false)
const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingDatabase = ref(null)
const queryTestRef = ref(null)

const toast = ref({
  show: false,
  message: '',
  type: 'success'
})

const normalizeDatabase = (db) => {
  if (!db) return null
  return {
    ...db,
    id: db.db_id || db.id
  }
}

onMounted(() => {
  loadDatabases()
})

const loadDatabases = async () => {
  isLoading.value = true
  try {
    const response = await knowledgeApi.getDatabases()
    const rawDatabases = response.data.databases || []
    databases.value = rawDatabases.map(db => normalizeDatabase(db)).filter(db => db !== null)
  } catch (error) {
    console.error('Failed to load databases:', error)
    showToast('Failed to load knowledge bases', 'error')
  } finally {
    isLoading.value = false
  }
}

const handleSelectDatabase = async (database) => {
  if (selectedDatabaseId.value === database.id) {
    selectedDatabaseId.value = ''
    selectedDatabase.value = null
    return
  }

  selectedDatabaseId.value = database.id
  selectedDatabase.value = database

  if (queryTestRef.value) {
    queryTestRef.value.clearResults()
  }
}

const handleDeleteDatabase = async (database) => {
  if (!confirm(`Delete knowledge base "${database.name}"? This cannot be undone.`)) {
    return
  }

  try {
    const dbIdToDelete = database.db_id || database.id
    await knowledgeApi.deleteDatabase(dbIdToDelete)

    if (selectedDatabaseId.value === database.id) {
      selectedDatabaseId.value = ''
      selectedDatabase.value = null
    }

    await loadDatabases()
    showToast('Knowledge base deleted', 'success')
  } catch (error) {
    console.error('Failed to delete:', error)
    showToast('Failed to delete knowledge base', 'error')
  }
}

const handleEditDatabase = (database) => {
  editingDatabase.value = database
  showEditModal.value = true
}

const handleUpdateDatabase = async (data) => {
  try {
    const dbId = editingDatabase.value.db_id || editingDatabase.value.id
    await knowledgeApi.updateDatabase(dbId, {
      name: data.database_name,
      description: data.description
    })
    await loadDatabases()
    showToast('Knowledge base updated', 'success')
  } catch (error) {
    console.error('Failed to update:', error)
    showToast('Failed to update knowledge base', 'error')
    throw error
  }
}

const handleCreateDatabase = async (data) => {
  try {
    const response = await knowledgeApi.createDatabase(data)
    await loadDatabases()
    showToast('Knowledge base created', 'success')
  } catch (error) {
    console.error('Failed to create:', error)
    showToast('Failed to create knowledge base', 'error')
    throw error
  }
}

const handleUploadComplete = (file) => {
  showToast(`File "${file.name}" added to knowledge base`, 'success')
}

const handleFileUploaded = (file) => {
  showToast(`File "${file.name}" uploaded. Click "Add to KB" to add it to the knowledge base.`, 'success')
}

const handleUploadError = (file) => {
  showToast(`Failed to process "${file.name}": ${file.error || 'Unknown error'}`, 'error')
}

const showToast = (message, type = 'success') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}
</script>

<style scoped>
.library-studio {
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

.create-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  border: none;
  border-radius: var(--radius-lg);
  color: var(--color-bg-primary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.create-btn svg {
  width: 18px;
  height: 18px);
}

/* Content Wrapper */
.content-wrapper {
  min-height: 500px);
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
  height: 40px);
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

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: var(--space-6);
}

/* Databases Panel */
.databases-panel {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.panel-title {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--color-text-primary);
}

.panel-count {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.databases-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

/* Side Panel */
.side-panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.side-panel.empty {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-selection {
  text-align: center;
}

.empty-selection .empty-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto var(--space-4);
  background: var(--color-bg-elevated);
}

.empty-selection h4 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-selection p {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.panel-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.panel-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.panel-card-header svg {
  width: 20px;
  height: 20px;
  color: var(--color-accent-primary);
}

.panel-card-header h3 {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Toast */
.toast {
  position: fixed;
  top: var(--space-6);
  right: var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-lg);
  color: white;
  font-size: var(--text-sm);
  z-index: 1000;
  animation: slideInRight var(--transition-base);
}

.toast.success {
  background: var(--color-success);
}

.toast.error {
  background: var(--color-error);
}

.toast svg {
  width: 18px;
  height: 18px);
}

.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-base);
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

/* Responsive */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .databases-list {
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  }
}

@media (max-width: 768px) {
  .studio-header {
    flex-direction: column;
    gap: var(--space-4);
  }

  .create-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
