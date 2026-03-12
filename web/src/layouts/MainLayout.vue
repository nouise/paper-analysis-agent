<template>
  <div class="main-layout">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <main class="main-content" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import Sidebar from '../components/Sidebar.vue'

const sidebarCollapsed = ref(false)

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// Handle window resize
const handleResize = () => {
  if (window.innerWidth < 1024) {
    sidebarCollapsed.value = true
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  display: flex;
  width: 100%;
  height: 100vh;
  background: var(--color-bg-primary);
  overflow: hidden;
}

.main-content {
  flex: 1;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-8);
  transition: padding var(--transition-base);
}

/* Page Transition */
.page-enter-active,
.page-leave-active {
  transition: all var(--transition-base);
}

.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
