import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, researchTopics } from '../services/api'
import {
  ArrowRight, Activity, Clock, FileText, Lightbulb, Mic, RefreshCw,
  Sparkles, TrendingUp, Upload, Video, WandSparkles,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

const quickActions = [
  { to: '/scripts', icon: FileText, title: 'Write a script', detail: 'Turn a topic into a ready-to-record script' },
  { to: '/voice', icon: Mic, title: 'Create a voiceover', detail: 'Narrate your script with text-to-speech' },
  { to: '/videos', icon: Video, title: 'Build a video', detail: 'Combine a script, voice, and visuals' },
]

export default function Overview() {
  const [stats, setStats] = useState(null)
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [topicError, setTopicError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let active = true

    async function loadDashboard() {
      setLoading(true)
      setError('')
      setTopicError('')

      const [dashboardResult, topicResult] = await Promise.allSettled([
        getDashboard(),
        researchTopics('technology'),
      ])

      if (!active) return

      if (dashboardResult.status === 'fulfilled') {
        setStats(dashboardResult.value.data)
      } else {
        setError('We couldn’t load your dashboard. Check that the backend is running, then try again.')
      }

      if (topicResult.status === 'fulfilled') {
        setTopics(topicResult.value.data.suggestions || [])
      } else {
        setTopics([])
        setTopicError('Topic ideas are temporarily unavailable.')
      }

      setLoading(false)
    }

    loadDashboard()
    return () => { active = false }
  }, [refreshKey])

  const cards = [
    { label: 'Scripts', value: stats?.total_scripts || 0, icon: FileText, gradient: 'linear-gradient(135deg,#22d3ee,#38bdf8)', to: '/scripts' },
    { label: 'Videos', value: stats?.total_videos || 0, icon: Video, gradient: 'linear-gradient(135deg,#818cf8,#a78bfa)', to: '/videos' },
    { label: 'Uploads', value: stats?.total_uploads || 0, icon: Upload, gradient: 'linear-gradient(135deg,#34d399,#2dd4bf)', to: '/uploads' },
    { label: 'Needs review', value: stats?.pending_approvals || 0, icon: Clock, gradient: 'linear-gradient(135deg,#fbbf24,#f59e0b)', to: '/uploads' },
  ]

  const chartData = [
    { name: 'Scripts', count: stats?.total_scripts || 0 },
    { name: 'Videos', count: stats?.total_videos || 0 },
    { name: 'Uploads', count: stats?.total_uploads || 0 },
    { name: 'Schedules', count: stats?.active_schedules || 0 },
  ]

  if (loading && !stats) {
    return (
      <div className="yc-loading-state" role="status">
        <span className="yc-loading-spinner" />
        <span>Getting your workspace ready…</span>
      </div>
    )
  }

  return (
    <div className="yc-dashboard">
      <section className="yc-dashboard-hero">
        <div>
          <span className="yc-eyebrow"><Sparkles size={14} /> YOUR CREATOR WORKSPACE</span>
          <h1 className="yc-page-title">Make your next video</h1>
          <p className="yc-page-sub">Plan, create, and publish YouTube content from one place.</p>
        </div>
        <Link to="/scripts" className="yc-btn yc-btn-primary">
          <WandSparkles size={17} /> Start creating
        </Link>
      </section>

      {error && (
        <div className="yc-alert" role="alert">
          <span>{error}</span>
          <button className="yc-btn yc-btn-ghost" onClick={() => setRefreshKey((key) => key + 1)}>
            <RefreshCw size={15} /> Try again
          </button>
        </div>
      )}

      <section className="yc-quick-start" aria-labelledby="quick-start-title">
        <div className="yc-section-heading">
          <div>
            <h2 id="quick-start-title">Create something</h2>
            <p>Choose a step to get started. Your work saves automatically.</p>
          </div>
        </div>
        <div className="yc-quick-grid">
          {quickActions.map(({ to, icon: Icon, title, detail }, index) => (
            <Link to={to} className="yc-quick-link" key={to}>
              <span className="yc-quick-icon"><Icon size={19} /></span>
              <span className="yc-quick-copy">
                <span className="yc-quick-title">{title}</span>
                <span className="yc-quick-detail">{detail}</span>
              </span>
              <ArrowRight size={17} className="yc-quick-arrow" />
              <span className="yc-quick-number">0{index + 1}</span>
            </Link>
          ))}
        </div>
      </section>

      <section aria-label="Content overview">
        <div className="yc-section-heading">
          <div>
            <h2>Your content</h2>
            <p>A quick look at what you’ve made so far.</p>
          </div>
          {loading && <span className="yc-subtle-status">Updating…</span>}
        </div>
        <div className="yc-stats-grid">
          {cards.map(({ label, value, icon: Icon, gradient, to }) => (
            <Link key={label} to={to} className="yc-card-stat yc-stat-link">
              <div className="yc-stat-info">
                <span className="yc-stat-label">{label}</span>
                <span className="yc-stat-value">{value}</span>
              </div>
              <span className="yc-stat-icon" style={{ background: gradient }}>
                <Icon size={20} color="#020617" strokeWidth={2.2} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      <div className="yc-dashboard-grid">
        <section className="yc-panel yc-dashboard-panel">
          <div className="yc-section-heading">
            <div>
              <h2><TrendingUp size={17} /> Content stats</h2>
              <p>Scripts, videos, uploads, and schedules</p>
            </div>
          </div>
          {chartData.every((item) => item.count === 0) ? (
            <div className="yc-empty yc-chart-empty">
              <FileText size={22} />
              <p>Your content totals will show here as you create.</p>
              <Link to="/scripts" className="yc-text-link">Create your first script <ArrowRight size={14} /></Link>
            </div>
          ) : (
            <div className="yc-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 10, fontSize: 12 }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Bar dataKey="count" fill="#22d3ee" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section className="yc-panel yc-dashboard-panel">
          <div className="yc-section-heading">
            <div>
              <h2><Lightbulb size={17} /> Topic ideas</h2>
              <p>Fresh inspiration for your next video</p>
            </div>
            <Link to="/calendar" className="yc-text-link">Explore <ArrowRight size={14} /></Link>
          </div>
          <div className="yc-topic-list">
            {topicError && <p className="yc-muted-message">{topicError} You can still create a script anytime.</p>}
            {!topicError && topics.length === 0 && (
              <p className="yc-muted-message">No ideas yet. Visit Content Ideas to explore topics.</p>
            )}
            {topics.slice(0, 5).map((topic, index) => (
              <div key={`${topic.topic}-${index}`} className="yc-topic-item">
                <span className="yc-topic-marker">{index + 1}</span>
                <div>
                  <div className="yc-topic-title">{topic.topic}</div>
                  <div className="yc-topic-reason">{topic.reason}</div>
                  {topic.estimated_interest && <span className="yc-chip">{topic.estimated_interest}</span>}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="yc-panel yc-dashboard-panel">
        <div className="yc-section-heading">
          <div>
            <h2><Activity size={17} /> Recent activity</h2>
            <p>Your latest work in this workspace</p>
          </div>
          <Link to="/history" className="yc-text-link">View history <ArrowRight size={14} /></Link>
        </div>
        {(stats?.recent_activity || []).length === 0 ? (
          <div className="yc-empty yc-activity-empty">
            <Activity size={22} />
            <p>No activity yet. Start with a script and your progress will appear here.</p>
          </div>
        ) : (
          <div className="yc-activity-list">
            {(stats?.recent_activity || []).slice(0, 8).map((log) => (
              <div key={log.id} className="yc-activity-row">
                <div>
                  <div className="yc-activity-action">{(log.action || 'Activity').replace(/_/g, ' ')}</div>
                  <div className="yc-activity-detail">
                    {log.entity_type || 'Workspace'} {log.entity_id ? `#${log.entity_id}` : ''}
                  </div>
                </div>
                <time className="yc-activity-time" dateTime={log.created_at}>
                  {new Date(log.created_at).toLocaleString()}
                </time>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
