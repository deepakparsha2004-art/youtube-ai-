import { useState, useEffect } from 'react'
import { connectYouTube, getChannel, disconnectYouTube } from '../services/api'
import { Youtube, Link2, Unlink, Loader2 } from 'lucide-react'

export default function YouTubeChannel() {
  const [channel, setChannel] = useState(null)
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getChannel().then((r) => setChannel(r.data)).catch(() => setChannel(null)).finally(() => setLoading(false))
  }, [])

  const handleConnect = async () => {
    setConnecting(true)
    setError('')
    try {
      const res = await connectYouTube()
      window.location.href = res.data.authorization_url
    } catch (err) {
      setError(err.response?.data?.detail || 'Configure Google OAuth in API Settings first')
      setConnecting(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Youtube size={24} color="#ef4444" /> YouTube Channel</h1>
        <p className="yc-page-sub">Connect your channel via secure Google OAuth</p>
      </div>

      <div className="yc-panel" style={{ padding: '1.75rem', maxWidth: 520 }}>
        {loading ? (
          <p style={{ color: 'var(--text-dim)' }}>Loading…</p>
        ) : channel?.is_connected ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              {channel.thumbnail_url && (
                <img src={channel.thumbnail_url} alt="" style={{ width: 56, height: 56, borderRadius: '50%', border: '2px solid var(--border-glow)' }} />
              )}
              <div>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700 }}>{channel.channel_title}</h3>
                <p style={{ margin: 0, fontSize: 11, color: 'var(--text-dim)' }}>{channel.channel_id}</p>
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              {[
                ['Subscribers', channel.subscriber_count?.toLocaleString()],
                ['Videos', channel.video_count],
                ['Views', (channel.view_count || 0).toLocaleString()],
              ].map(([label, val]) => (
                <div key={label} className="yc-card" style={{ textAlign: 'center', padding: '0.85rem' }}>
                  <div style={{ fontSize: 18, fontWeight: 800 }}>{val}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{label}</div>
                </div>
              ))}
            </div>
            <button className="yc-btn yc-btn-danger" onClick={async () => {
              if (confirm('Disconnect?')) { await disconnectYouTube(); setChannel(null) }
            }}>
              <Unlink size={16} /> Disconnect
            </button>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
            <Youtube size={48} style={{ color: '#475569', marginBottom: 12 }} />
            <p style={{ color: 'var(--text)', marginBottom: 12 }}>No channel connected</p>
            {error && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</p>}
            <button className="yc-btn" onClick={handleConnect} disabled={connecting}
              style={{ background: '#dc2626', color: '#fff', padding: '0.75rem 1.5rem' }}>
              {connecting ? <Loader2 className="animate-spin" size={18} /> : <Link2 size={18} />}
              Connect with Google
            </button>
            <p style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 14, maxWidth: 320, marginLeft: 'auto', marginRight: 'auto' }}>
              Requires Google Cloud OAuth credentials. See API Settings and README.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
