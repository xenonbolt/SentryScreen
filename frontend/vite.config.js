import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite config — SentryScreen Adverse Media Copilot
 * 
 * API proxy strategy:
 *   • Direct dev mode:   /api  →  http://localhost:8000/api
 *   • Jupyter notebook:  The frontend detects /proxy/<PORT>/ in the URL
 *     at runtime (in api/client.js) and constructs the full URL itself.
 *     No Vite proxy config is needed for Jupyter — the browser talks
 *     directly to the Jupyter server which proxies to the backend.
 */
export default defineConfig({
  base: './',
  plugins: [react()],
  server: {
    port: 8501,
    host: '0.0.0.0',
    proxy: {
      // Standard Vite dev server: proxy /api → FastAPI on port 8000
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // Strip /api prefix — FastAPI routes are mounted at /api/...
        // so keep as-is (FastAPI uses APIRouter with prefix="/api")
      },
    },
  },
  preview: {
    port: 8501,
    host: '0.0.0.0',
  },
})
