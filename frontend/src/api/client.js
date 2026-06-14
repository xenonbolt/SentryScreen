/**
 * api/client.js
 * ──────────────────────────────────────────────────────────────────────────
 * Smart API client that:
 *   1. Detects Jupyter notebook proxy (URL contains /proxy/<PORT>/)
 *   2. Falls back to relative /api prefix for direct Vite dev server
 *   3. Exposes `isDemoMode` flag when backend is unreachable
 *
 * Port reference (must match backend/.env → PORT):
 *   Backend FastAPI : 8000   ← backend/.env PORT=8000
 *   Frontend Vite   : 8501   ← vite.config.js server.port
 *   Jupyter proxy   : /proxy/8000/  (auto-detected at runtime below)
 */

// ── Single source of truth for the backend port ───────────────────────────────
// Keep this in sync with backend/.env → PORT=8000
export const BACKEND_PORT = 8000;

// ── Jupyter Proxy Detection ───────────────────────────────────────────────────
// When this app is served through a Jupyter notebook server the URL looks like:
//   http://localhost:8888/proxy/8000/  (Jupyter proxying to FastAPI on :8000)
// We detect that pattern and prepend it to every /api call automatically.
function detectApiBase() {
  // 1. Explicit cross-origin override via Command Line
  // e.g. VITE_API_BASE="https://notebooks.amd.com/.../proxy/8000/api" npm run dev
  if (import.meta.env.VITE_API_BASE) {
    // Trim trailing slashes to prevent //api issues
    return import.meta.env.VITE_API_BASE.replace(/\/+$/, '');
  }

  const { pathname, origin } = window.location;

  // 2. Auto-detect if UI is hosted directly behind Jupyter proxy
  // Match /proxy/<any-port>/ or /user/xxx/proxy/<any-port>/
  const proxyMatch = pathname.match(/^(.*\/proxy\/\d+)\//);
  if (proxyMatch) {
    // e.g.  origin/proxy/8000/api  →  http://localhost:8888/proxy/8000/api
    return `${origin}${proxyMatch[1]}/api`;
  }

  // 3. Standard Vite dev server: Vite proxies /api → http://localhost:8000/api
  // (configured in vite.config.js → server.proxy['/api'].target)
  return '/api';
}

export const API_BASE = detectApiBase();
export let isDemoMode = false;

async function request(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };

  // If the backend is behind a Jupyter proxy that requires auth,
  // pass VITE_JUPYTER_TOKEN=... via the command line to bypass the login wall.
  const jupyterToken = import.meta.env.VITE_JUPYTER_TOKEN;
  if (jupyterToken) {
    headers['Authorization'] = `token ${jupyterToken}`;
  }

  // Also support query param fallback for strict proxies
  const sep = path.includes('?') ? '&' : '?';
  const urlPath = jupyterToken ? `${path}${sep}token=${jupyterToken}` : path;

  try {
    const res = await fetch(`${API_BASE}${urlPath}`, {
      headers,
      ...options,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }
    isDemoMode = false;
    return res.json();
  } catch (err) {
    if (err.message?.includes('fetch') || err instanceof TypeError) {
      // Network failure → switch to demo mode
      isDemoMode = true;
    }
    throw err;
  }
}

/** Screen an entity for adverse media */
export async function screenEntity({ entity_name, top_k = 10, threshold = 0.15, use_live_web = false }) {
  return request('/screen', {
    method: 'POST',
    body: JSON.stringify({ entity_name, top_k, threshold, use_live_web }),
  });
}

/** Submit analyst decision */
export async function submitAudit({ screening_id, entity_name, action, analyst_notes, risk_score, risk_category }) {
  return request('/audit', {
    method: 'POST',
    body: JSON.stringify({ screening_id, entity_name, action, analyst_notes, risk_score, risk_category }),
  });
}

/** Fetch audit log */
export async function fetchAuditLog(limit = 50) {
  return request(`/audit-log?limit=${limit}`);
}

/** Health stats */
export async function fetchHealth() {
  return request('/health');
}

/** Rapid telemetry (VRAM, CPU, Load) */
export async function fetchTelemetry() {
  return request('/telemetry');
}

/** Dataset stats */
export async function fetchDatasetStats() {
  return request('/dataset-stats');
}

/** Fetch articles (compliance db) */
export async function fetchArticles(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return request(`/articles${qs ? '?' + qs : ''}`);
}
