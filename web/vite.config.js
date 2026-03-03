import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    allowedHosts: ['.natappfree.cc', '.natapp.cc'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/knowledge': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/send_input': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})