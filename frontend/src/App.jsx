import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import LoginScreen from './components/common/LoginScreen'
import DashboardLayout from './layouts/DashboardLayout'
import Overview from './pages/Overview'
import ScriptStudio from './pages/ScriptStudio'
import VoiceStudio from './pages/VoiceStudio'
import VideoGenerator from './pages/VideoGenerator'
import ThumbnailGenerator from './pages/ThumbnailGenerator'
import YouTubeChannel from './pages/YouTubeChannel'
import UploadManager from './pages/UploadManager'
import ContentCalendar from './pages/ContentCalendar'
import AutomationSettings from './pages/AutomationSettings'
import HistoryLogs from './pages/HistoryLogs'
import APISettings from './pages/APISettings'
import UserProfile from './pages/UserProfile'

export default function App() {
  const { user, loading, authRequired } = useAuth()

  if (authRequired && loading) {
    return <main aria-label="Loading" style={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>Loading…</main>
  }
  if (authRequired && !user) return <LoginScreen />

  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />}>
        <Route index element={<Overview />} />
        <Route path="scripts" element={<ScriptStudio />} />
        <Route path="voice" element={<VoiceStudio />} />
        <Route path="videos" element={<VideoGenerator />} />
        <Route path="thumbnails" element={<ThumbnailGenerator />} />
        <Route path="youtube" element={<YouTubeChannel />} />
        <Route path="uploads" element={<UploadManager />} />
        <Route path="calendar" element={<ContentCalendar />} />
        <Route path="automation" element={<AutomationSettings />} />
        <Route path="history" element={<HistoryLogs />} />
        <Route path="api-settings" element={<APISettings />} />
        <Route path="profile" element={<UserProfile />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
