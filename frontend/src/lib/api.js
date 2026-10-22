const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function getSessionId() {
  let id = sessionStorage.getItem('pricelens_session_id')
  if (!id) {
    id = crypto.randomUUID().replaceAll('-', '')
    sessionStorage.setItem('pricelens_session_id', id)
  }
  return id
}

export async function apiRequest(path, options = {}) {
  let response
  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', 'X-Session-ID': getSessionId(), ...(options.headers || {}) },
    })
  } catch {
    throw new Error(`Cannot connect to PriceLens API at ${API}. Start the FastAPI backend and check CORS settings.`)
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Please try again.`)
  return data
}

export const analyzeProduct = (url) => apiRequest('/api/analyze', { method: 'POST', body: JSON.stringify({ url }) })
export const ingestText = (payload) => apiRequest('/api/ingest-text', { method: 'POST', body: JSON.stringify(payload) })
export const askQuestion = (question, comparison_id) => apiRequest('/api/chat', { method: 'POST', body: JSON.stringify({ question, comparison_id }) })
