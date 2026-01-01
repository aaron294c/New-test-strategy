import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0', // Required for Codespaces/Docker port forwarding
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/stock': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/stocks': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/bins': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/recommendation': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/trade-management': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/position-calculator': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/comparison': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
