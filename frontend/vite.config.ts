import { defineConfig, createLogger } from 'vite'
import react from '@vitejs/plugin-react'

const logger = createLogger()
const originalWarn = logger.warn
const originalWarnOnce = logger.warnOnce

logger.warn = (msg, options) => {
  // 忽略 @splinetool/runtime 等第三方库动态加载 draco / wasm 时静态分析找不到文件的提示
  if (typeof msg === 'string' && msg.includes("doesn't exist at build time")) {
    return
  }
  originalWarn(msg, options)
}

logger.warnOnce = (msg, options) => {
  if (typeof msg === 'string' && msg.includes("doesn't exist at build time")) {
    return
  }
  originalWarnOnce(msg, options)
}

// https://vitejs.dev/config/
export default defineConfig({
  customLogger: logger,
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 1200,
    rollupOptions: {
      output: {
        manualChunks: {
          spline: ['@splinetool/react-spline', '@splinetool/runtime'],
          aggrid: ['ag-grid-community', 'ag-grid-react'],
          dnd: ['@dnd-kit/core', '@dnd-kit/sortable', '@dnd-kit/utilities'],
        }
      }
    }
  }
})

