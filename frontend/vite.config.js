import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Custom Vite Plugin to support Jupyter Proxy dynamically.
 * 
 * When running in Vite Dev Mode behind a Jupyter proxy, the browser asks for:
 *   GET /jupyter-hack-team-3033-xxx/proxy/8501/src/main.jsx
 * 
 * Vite natively expects:
 *   GET /src/main.jsx
 * 
 * This middleware strips everything up to the port number so Vite can
 * serve the files correctly without us needing to hardcode your workspace ID!
 */
const jupyterProxyPlugin = () => {
  return {
    name: 'jupyter-proxy-stripper',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const match = req.url.match(/^.*\/proxy\/\d+(\/.*)$/);
        if (match) {
          req.url = match[1] || '/';
        }
        next();
      });
    }
  }
}

export default defineConfig({
  base: './', // Ensure relative paths for production build
  plugins: [react(), jupyterProxyPlugin()],
  server: {
    port: 8501,
    host: '0.0.0.0',
    // We need to allow the specific Jupyter host (or all hosts)
    allowedHosts: 'all', 
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
    // Force HMR websocket to use the proxy path so hot-reloading works
    hmr: {
      clientPort: 443, // Notebooks use HTTPS
    }
  },
  preview: {
    port: 8501,
    host: '0.0.0.0',
    allowedHosts: 'all',
  },
})
