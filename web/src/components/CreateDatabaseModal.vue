<template>
  <div v-if="isVisible" class="modal-overlay" @click.self="close">
    <div class="modal-content">
      <div class="modal-header">
        <h3>{{ isEditMode ? 'Edit Knowledge Base' : 'Create Knowledge Base' }}</h3>
        <button class="close-btn" @click="close">×</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>Name <span class="required">*</span></label>
          <div class="name-input-wrapper">
            <input
              v-model="formData.name"
              type="text"
              placeholder="Enter knowledge base name"
              :class="{ error: errors.name }"
              @blur="validateName"
            />
            <button
              v-if="!isEditMode"
              type="button"
              class="random-name-btn"
              @click="generateRandomName"
              :disabled="isGeneratingName"
            >
              <span v-if="isGeneratingName" class="btn-spinner"></span>
              <span v-else>🎲</span>
            </button>
          </div>
          <span v-if="errors.name" class="error-text">{{ errors.name }}</span>
        </div>

        <div v-if="!isEditMode" class="form-group">
          <label>Name Style</label>
          <div class="style-selector">
            <button
              v-for="style in nameStyles"
              :key="style.value"
              type="button"
              class="style-btn"
              :class="{ active: selectedStyle === style.value }"
              @click="selectedStyle = style.value"
            >
              {{ style.label }}
            </button>
          </div>
          <span class="style-hint">{{ currentStyleHint }}</span>
        </div>

        <div class="form-group">
          <label>Description</label>
          <textarea
            v-model="formData.description"
            placeholder="Enter description (optional)"
            rows="3"
          ></textarea>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn-secondary" @click="close">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            <span v-if="isSubmitting" class="spinner"></span>
            {{ isSubmitting ? (isEditMode ? 'Saving...' : 'Creating...') : (isEditMode ? 'Save' : 'Create') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'

const generateRandomName = async () => {
  isGeneratingName.value = true
  try {
    const response = await fetch(`/knowledge/generate-name?style=${selectedStyle.value}`)
    const data = await response.json()
    if (data.status === 'success') {
      formData.name = data.name
      errors.name = ''
    } else {
      console.error('Failed to generate name:', data.message)
    }
  } catch (error) {
    console.error('Error generating name:', error)
  } finally {
    isGeneratingName.value = false
  }
}

const props = defineProps({
  visible: { type: Boolean, default: false },
  database: { type: Object, default: null },
  mode: { type: String, default: 'create' } // 'create' or 'edit'
})

const emit = defineEmits(['update:visible', 'submit'])

const isVisible = ref(false)
const isSubmitting = ref(false)
const isGeneratingName = ref(false)
const selectedStyle = ref('academic')
const formData = reactive({ name: '', description: '' })
const errors = reactive({ name: '' })

const isEditMode = computed(() => props.mode === 'edit')

const nameStyles = [
  { value: 'academic', label: 'Academic', example: 'Deep Learning Research_0311' },
  { value: 'random', label: 'Random', example: 'Smart Knowledge_a3f9' },
  { value: 'timestamp', label: 'Timestamp', example: 'KB_20250311_143052' },
  { value: 'simple', label: 'Simple', example: 'NLP Study_8472' }
]

const currentStyleHint = computed(() => {
  const style = nameStyles.find(s => s.value === selectedStyle.value)
  return style ? `Example: ${style.example}` : ''
})

watch(() => props.visible, (newVal) => {
  isVisible.value = newVal
  if (newVal) resetForm()
})

watch(() => props.database, (newVal) => {
  if (isEditMode.value && newVal && isVisible.value) {
    formData.name = newVal.name || ''
    formData.description = newVal.description || ''
  }
})

const resetForm = () => {
  if (isEditMode.value && props.database) {
    formData.name = props.database.name || ''
    formData.description = props.database.description || ''
  } else {
    formData.name = ''
    formData.description = ''
    selectedStyle.value = 'academic'
  }
  errors.name = ''
}

const validateName = () => {
  if (!formData.name.trim()) {
    errors.name = 'Name is required'
    return false
  }
  if (formData.name.length < 2) {
    errors.name = 'Name must be at least 2 characters'
    return false
  }
  if (formData.name.length > 50) {
    errors.name = 'Name must be less than 50 characters'
    return false
  }
  errors.name = ''
  return true
}

const handleSubmit = async () => {
  if (!validateName()) return

  isSubmitting.value = true
  try {
    await emit('submit', {
      database_name: formData.name,
      description: formData.description
    })
    close()
  } catch (error) {
    console.error(isEditMode.value ? 'Failed to update:' : 'Failed to create:', error)
  } finally {
    isSubmitting.value = false
  }
}

const close = () => {
  isVisible.value = false
  emit('update:visible', false)
}
</script>

<style scoped>
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
  max-width: 480px;
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

form {
  padding: var(--space-5);
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

.required {
  color: var(--color-error);
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  font-size: var(--text-base);
  transition: all var(--transition-fast);
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 0 3px var(--color-accent-glow);
}

.form-group input.error {
  border-color: var(--color-error);
}

/* Name Input with Random Button */
.name-input-wrapper {
  display: flex;
  gap: var(--space-2);
}

.name-input-wrapper input {
  flex: 1;
}

.random-name-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-text-secondary);
  font-size: var(--text-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.random-name-btn:hover:not(:disabled) {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.random-name-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Style Selector */
.style-selector {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.style-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-primary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.style-btn:hover {
  border-color: var(--color-border-hover);
  color: var(--color-text-primary);
}

.style-btn.active {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.style-hint {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-text-muted);
}

.error-text {
  display: block;
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  color: var(--color-error);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding-top: var(--space-5);
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
  display: flex;
  align-items: center;
  gap: var(--space-2);
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

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(10, 10, 15, 0.3);
  border-top-color: var(--color-bg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
</style>
