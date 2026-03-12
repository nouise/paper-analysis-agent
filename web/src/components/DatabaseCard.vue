<template>
  <div
    class="database-card"
    :class="{ selected: isSelected }"
    @click="$emit('select', database)"
  >
    <div class="card-header">
      <div class="card-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <ellipse cx="12" cy="5" rx="9" ry="3"/>
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
        </svg>
      </div>
      <div class="card-actions">
        <button
          class="action-btn edit-btn"
          @click.stop="$emit('edit', database)"
          title="Edit"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
        </button>
        <button
          class="action-btn delete-btn"
          @click.stop="$emit('delete', database)"
          title="Delete"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="card-content">
      <h3 class="database-name">{{ database.name }}</h3>
      <p class="database-desc">{{ database.description || 'No description' }}</p>
    </div>

    <div class="card-footer">
      <div class="footer-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span>{{ database.document_count || 0 }} docs</span>
      </div>
      <div class="footer-item">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span>{{ formatDate(database.created_at) }}</span>
      </div>
    </div>

    <div v-if="isSelected" class="selected-indicator"></div>
  </div>
</template>

<script setup>
const props = defineProps({
  database: { type: Object, required: true },
  isSelected: { type: Boolean, default: false }
})

defineEmits(['select', 'delete', 'edit'])

const formatDate = (date) => {
  if (!date) return 'Unknown'
  const d = new Date(date)
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>

<style scoped>
.database-card {
  position: relative;
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.database-card:hover {
  border-color: var(--color-border-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.database-card.selected {
  border-color: var(--color-accent-primary);
  background: var(--color-accent-glow);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.card-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent-glow);
  border-radius: var(--radius-lg);
  color: var(--color-accent-primary);
}

.card-icon svg {
  width: 20px;
  height: 20px);
}

.delete-btn {
  width: 28px;
  height: 28px;
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

.database-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--color-error-bg);
  border-color: var(--color-error);
  color: var(--color-error);
}

.delete-btn svg {
  width: 14px;
  height: 14px);
}

.card-actions {
  display: flex;
  gap: var(--space-2);
}

.action-btn {
  width: 28px;
  height: 28px;
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

.database-card:hover .action-btn {
  opacity: 1;
}

.action-btn:hover {
  background: var(--color-bg-elevated);
  border-color: var(--color-border);
  color: var(--color-text-primary);
}

.action-btn.edit-btn:hover {
  background: var(--color-accent-glow);
  border-color: var(--color-accent-primary);
  color: var(--color-accent-primary);
}

.action-btn.delete-btn:hover {
  background: var(--color-error-bg);
  border-color: var(--color-error);
  color: var(--color-error);
}

.action-btn svg {
  width: 14px;
  height: 14px);
}

.card-content {
  margin-bottom: var(--space-4);
}

.database-name {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  line-height: 1.3;
}

.database-desc {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
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
  height: 14px);
}

.selected-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 40px;
  background: var(--color-accent-primary);
  border-radius: 0 3px 3px 0;
}
</style>
