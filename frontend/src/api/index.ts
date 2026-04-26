/** axios 封装 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 响应拦截：直接返回 data
api.interceptors.response.use(
  (res) => res.data,
  (err) => {
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default api

// 会话 API
export const sessionsApi = {
  list: () => api.get('/sessions'),
  create: () => api.post('/sessions'),
  get: (id: string) => api.get(`/sessions/${id}`),
  delete: (id: string) => api.delete(`/sessions/${id}`),
  update: (id: string, data: { title: string }) => api.patch(`/sessions/${id}`, data),
}

// 笔记 API
export const notesApi = {
  list: (sessionId?: string) => api.get('/notes', { params: { session_id: sessionId } }),
  get: (id: number) => api.get(`/notes/${id}`),
  download: (id: number) => `/api/notes/${id}/download`,
  delete: (id: number) => api.delete(`/notes/${id}`),
}

// 日志 API
export const logsApi = {
  list: (limit?: number, sessionId?: string) => api.get('/logs', { params: { limit, session_id: sessionId } }),
  stats: (sessionId?: string) => api.get('/logs/stats', { params: { session_id: sessionId } }),
  timeline: (sessionId?: string) => api.get('/logs/timeline', { params: { session_id: sessionId } }),
  tools: (sessionId?: string) => api.get('/logs/tools', { params: { session_id: sessionId } }),
}
