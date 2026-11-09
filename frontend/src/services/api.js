import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

const TOKEN_KEY = 'youtube-ai-access-token'

api.interceptors.request.use((config) => {
  const token = window.sessionStorage.getItem(TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.sessionStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new Event('auth:unauthorized'))
    }
    return Promise.reject(error)
  },
)

export default api
export { TOKEN_KEY }

// Scripts
export const generateScript = (data) => api.post('/scripts/generate', data)
export const listScripts = () => api.get('/scripts/')
export const getScript = (id) => api.get(`/scripts/${id}`)
export const updateScript = (id, data) => api.patch(`/scripts/${id}`, data)
export const deleteScript = (id) => api.delete(`/scripts/${id}`)
export const improveScript = (id, instruction) =>
  api.post(`/scripts/${id}/improve?instruction=${encodeURIComponent(instruction)}`)

// Voice
export const listVoices = () => api.get('/voice/voices')
export const recommendedVoices = () => api.get('/voice/recommended')
export const generateVoice = (data) => api.post('/voice/generate', data)
export const getAudioFile = (filename) =>
  api.get(`/voice/audio/${encodeURIComponent(filename)}`, { responseType: 'blob' })

// Videos
export const createVideo = (data) => api.post('/videos/create', data)
export const generateFalVideo = (data) => api.post('/videos/generate-ai', data)
export const listVideos = () => api.get('/videos/')
export const getVideo = (id) => api.get(`/videos/${id}`)
export const createThumbnail = (id, data) => api.post(`/videos/${id}/thumbnail`, data)
export const getVideoFile = (id) => api.get(`/videos/${id}/file`, { responseType: 'blob' })
export const getThumbnailFile = (id) =>
  api.get(`/videos/${id}/thumbnail-file`, { responseType: 'blob' })
export const deleteVideo = (id) => api.delete(`/videos/${id}`)

// YouTube
export const connectYouTube = () => api.get('/youtube/connect')
export const getChannel = () => api.get('/youtube/channel')
export const uploadVideo = (data) => api.post('/youtube/upload', data)
export const listUploads = () => api.get('/youtube/uploads')
export const disconnectYouTube = () => api.delete('/youtube/disconnect')

// Scheduler
export const createSchedule = (data) => api.post('/scheduler/', data)
export const listSchedules = () => api.get('/scheduler/')
export const toggleSchedule = (id, active) =>
  api.patch(`/scheduler/${id}/toggle?active=${active}`)
export const deleteSchedule = (id) => api.delete(`/scheduler/${id}`)

// Analytics
export const getDashboard = () => api.get('/analytics/dashboard')
export const getLogs = () => api.get('/analytics/logs')
export const researchTopics = (niche = 'technology') =>
  api.get(`/analytics/research?niche=${encodeURIComponent(niche)}`)

// Settings
export const getSystemStatus = () => api.get('/settings/status')
