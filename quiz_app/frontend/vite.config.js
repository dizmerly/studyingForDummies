import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'node:path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      input: {
        index: resolve(import.meta.dirname, 'index.html'),
        pricing: resolve(import.meta.dirname, 'pricing.html'),
        login: resolve(import.meta.dirname, 'login.html'),
      },
    },
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:5001',
    },
  },
})
