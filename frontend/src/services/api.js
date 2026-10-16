const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

async function getCameraFrame() {
  const response = await fetch(`${API_URL}/api/camera/frame`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Camera frame unavailable: ${response.status}`);
  }
  const blob = await response.blob();
  if (!blob || blob.size === 0) {
    return '';
  }
  return URL.createObjectURL(blob);
}

export const api = {
  getHealth: () => request('/api/health'),
  getMonitoringStatus: () => request('/api/monitoring/status'),
  startMonitoring: () => request('/api/monitoring/start', { method: 'POST' }),
  stopMonitoring: () => request('/api/monitoring/stop', { method: 'POST' }),
  getSessions: () => request('/api/sessions'),
  getSession: (id) => request(`/api/sessions/${encodeURIComponent(id)}`),
  getSessionEvents: (id) => request(`/api/sessions/${encodeURIComponent(id)}/events`),
  deleteSession: (id) => request(`/api/sessions/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  getRecentEvents: () => request('/api/events/recent'),
  getCameraFrame,
};

export { API_URL };
