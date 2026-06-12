/**
 * api/client.js — Typed API client for the FastAPI backend
 */

const BASE = './api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

/** Screen an entity for adverse media */
export async function screenEntity({ entity_name, top_k = 10, threshold = 0.2, use_live_web = false }) {
  return request('/screen', {
    method: 'POST',
    body: JSON.stringify({ entity_name, top_k, threshold, use_live_web }),
  })
}

/** Submit analyst decision */
export async function submitAudit({ screening_id, entity_name, action, analyst_notes, risk_score, risk_category }) {
  return request('/audit', {
    method: 'POST',
    body: JSON.stringify({ screening_id, entity_name, action, analyst_notes, risk_score, risk_category }),
  })
}

/** Fetch audit log */
export async function fetchAuditLog(limit = 50) {
  return request(`/audit-log?limit=${limit}`)
}

/** Health check */
export async function fetchHealth() {
  return request('/health')
}

/** Dataset stats */
export async function fetchDatasetStats() {
  return request('/dataset-stats')
}
