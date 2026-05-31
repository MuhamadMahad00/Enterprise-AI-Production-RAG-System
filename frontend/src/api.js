const API_BASE = 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'API request failed');
  }
  return response.json();
}

export const api = {
  // Query
  query: (query) => request('/query', { method: 'POST', body: JSON.stringify({ query }) }),

  // Health & Metrics
  health: () => request('/health'),
  metrics: () => request('/metrics'),
  latencyBreakdown: () => request('/metrics/latency-breakdown'),

  // Documents
  listDocuments: () => request('/documents'),
  ingest: (data) => request('/ingest', { method: 'POST', body: JSON.stringify(data) }),
  reindex: () => request('/reindex', { method: 'POST' }),

  // Upload
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE}/upload`, { method: 'POST', body: formData });
    if (!response.ok) throw new Error('Upload failed');
    return response.json();
  },

  // Evaluation
  evaluate: (maxQuestions) =>
    request('/evaluate', {
      method: 'POST',
      body: JSON.stringify({ max_questions: maxQuestions }),
    }),
  getReport: () => request('/evaluation/report'),
  listReports: () => request('/evaluation/reports'),
};
