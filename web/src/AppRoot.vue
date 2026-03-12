<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
</script>

<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ========================================
   Design System - Research Atelier
   A sophisticated academic research interface
   ======================================== */

:root {
  /* Primary Colors - Deep Academic */
  --color-bg-primary: #0a0a0f;
  --color-bg-secondary: #12121a;
  --color-bg-tertiary: #1a1a25;
  --color-bg-elevated: #222230;
  --color-bg-card: #181824;

  /* Accent Colors - Warm Gold/Amber */
  --color-accent-primary: #d4a574;
  --color-accent-secondary: #c9a86c;
  --color-accent-hover: #e4b584;
  --color-accent-muted: #8b7355;
  --color-accent-glow: rgba(212, 165, 116, 0.15);

  /* Text Colors */
  --color-text-primary: #f5f3f0;
  --color-text-secondary: #b8b4ae;
  --color-text-muted: #7a756d;
  --color-text-disabled: #4a4744;

  /* Border Colors */
  --color-border: rgba(212, 165, 116, 0.12);
  --color-border-hover: rgba(212, 165, 116, 0.25);
  --color-border-active: rgba(212, 165, 116, 0.4);

  /* Status Colors */
  --color-success: #7ca782;
  --color-success-bg: rgba(124, 167, 130, 0.1);
  --color-error: #c97b7b;
  --color-error-bg: rgba(201, 123, 123, 0.1);
  --color-warning: #d4a574;
  --color-warning-bg: rgba(212, 165, 116, 0.1);
  --color-info: #6b8cae;
  --color-info-bg: rgba(107, 140, 174, 0.1);

  /* Typography */
  --font-display: 'Playfair Display', Georgia, serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Font Sizes */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 2rem;
  --text-4xl: 2.5rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-20: 5rem;

  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3);
  --shadow-glow: 0 0 20px rgba(212, 165, 116, 0.15);

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* ========================================
   Base Styles
   ======================================== */

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

html, body, #app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

body {
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: 1.6;
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ========================================
   Scrollbar Styles
   ======================================== */

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-full);
}

::-webkit-scrollbar-thumb {
  background: var(--color-border-hover);
  border-radius: var(--radius-full);
  border: 2px solid var(--color-bg-secondary);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-accent-muted);
}

/* ========================================
   Typography Utilities
   ======================================== */

.font-display {
  font-family: var(--font-display);
}

.font-mono {
  font-family: var(--font-mono);
}

.text-gradient {
  background: linear-gradient(135deg, var(--color-accent-primary), var(--color-accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ========================================
   Animation Keyframes
   ======================================== */

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 5px var(--color-accent-glow); }
  50% { box-shadow: 0 0 20px var(--color-accent-glow), 0 0 30px var(--color-accent-glow); }
}

/* ========================================
   Utility Classes
   ======================================== */

.animate-fade-in {
  animation: fadeIn var(--transition-base) ease-out;
}

.animate-fade-in-up {
  animation: fadeInUp var(--transition-slow) ease-out;
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
