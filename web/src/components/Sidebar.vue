<template>
  <aside class="sidebar" :class="{ 'collapsed': collapsed }">
    <!-- Brand -->
    <div class="sidebar-brand">
      <div class="brand-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
      </div>
      <div class="brand-text" v-if="!collapsed">
        <span class="brand-title">Paper Agent</span>
        <span class="brand-subtitle">Research Atelier</span>
      </div>
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div class="nav-section">
        <span class="nav-label" v-if="!collapsed">Research</span>
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ 'active': isActive(item.path) }"
          @click="navigate(item.path)"
        >
          <div class="nav-icon-wrapper">
            <component :is="item.icon" class="nav-icon" />
          </div>
          <span class="nav-text" v-if="!collapsed">{{ item.title }}</span>
          <div class="nav-indicator" v-if="isActive(item.path)"></div>
        </div>
      </div>
    </nav>

    <!-- Toggle Button -->
    <button class="toggle-btn" @click="toggle" :title="collapsed ? 'Expand' : 'Collapse'">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'flipped': collapsed }">
        <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5"/>
      </svg>
    </button>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Icon Components
const IconHome = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`
}

const IconHistory = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`
}

const IconLibrary = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>`
}

const IconWeChat = {
  template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 01-.9 3.8 8.5 8.5 0 01-7.6 4.7 8.38 8.38 0 01-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 01-.9-3.8 8.5 8.5 0 014.7-7.6 8.38 8.38 0 013.8-.9h.5a8.48 8.48 0 018 8v.5z"/></svg>`
}

const props = defineProps({
  collapsed: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle'])

const route = useRoute()
const router = useRouter()

const menuItems = [
  { title: 'New Research', path: '/', icon: IconHome },
  { title: 'History', path: '/history', icon: IconHistory },
  { title: 'Library', path: '/knowledge', icon: IconLibrary },
  { title: 'WeChat', path: '/wechat', icon: IconWeChat }
]

const isActive = (path) => route.path === path

const toggle = () => emit('toggle')
const navigate = (path) => router.push(path)
</script>

<style scoped>
.sidebar {
  width: 260px;
  height: 100%;
  background: linear-gradient(180deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  position: relative;
  transition: width var(--transition-slow);
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 72px;
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.brand-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  border-radius: var(--radius-lg);
  color: var(--color-bg-primary);
  flex-shrink: 0;
}

.brand-icon svg {
  width: 22px;
  height: 22px;
}

.brand-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: opacity var(--transition-base);
}

.sidebar.collapsed .brand-text {
  opacity: 0;
  width: 0;
}

.brand-title {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.brand-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: var(--space-6) var(--space-4);
  overflow-y: auto;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.nav-label {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 0 var(--space-3);
  margin-bottom: var(--space-2);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  position: relative;
  transition: all var(--transition-fast);
  color: var(--color-text-secondary);
}

.nav-item:hover {
  background: var(--color-bg-elevated);
  color: var(--color-text-primary);
}

.nav-item.active {
  background: var(--color-accent-glow);
  color: var(--color-accent-primary);
}

.nav-icon-wrapper {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon {
  width: 20px;
  height: 20px;
}

.nav-text {
  font-size: var(--text-sm);
  font-weight: 500;
  transition: opacity var(--transition-base);
}

.nav-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--color-accent-primary);
  border-radius: 0 3px 3px 0;
}

/* Toggle Button */
.toggle-btn {
  position: absolute;
  right: -12px;
  top: 80px;
  width: 24px;
  height: 24px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-muted);
  transition: all var(--transition-fast);
  z-index: 10;
}

.toggle-btn:hover {
  background: var(--color-accent-primary);
  border-color: var(--color-accent-primary);
  color: var(--color-bg-primary);
}

.toggle-btn svg {
  width: 14px;
  height: 14px;
  transition: transform var(--transition-base);
}

.toggle-btn svg.flipped {
  transform: rotate(180deg);
}
</style>
