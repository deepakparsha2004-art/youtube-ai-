import { useState, useEffect } from 'react'
import { listVideos, listUploads, uploadVideo, getChannel } from '../services/api'
import { Upload, Loader2, ExternalLink } from 'lucide-react'

export default function UploadManager() {
  const [videos, setVideos] = useState([])
  const [uploads, setUploads] = useState([])
  const [channel, setChannel] = useState(null)
  const [form, setForm] = useState({ video_id: '', visibility: 'private', approve: false })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    listVideos().then((r) => setVideos(r.data.filter((v) => v.video_path))).catch(console.error)
    listUploads().then((r) => setUploads(r.data)).catch(console.error)
    getChannel().then((r) => setChannel(r.data)).catch(() => {})
  }, [])

  const handleUpload = async (e) => {
    e.preventDefault()
    if (!channel) { setError('Connect a YouTube channel first'); return }
    if (form.visibility === 'public' && !form.approve) { setError('You must approve public uploads'); return }
    setLoading(true); setError(''); setSuccess('')
    try {
      const res = await uploadVideo({
        video_id: Number(form.video_id), channel_id: channel.id,
        visibility: form.visibility, approve: form.approve,
      })
      setSuccess(`Uploaded! ${res.data.youtube_url || res.data.status}`)
      listUploads().then((r) => setUploads(r.data))
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Upload size={24} color="var(--accent)" /> Upload Manager</h1>
        <p className="yc-page-sub">Upload videos to YouTube with approval controls</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        <form onSubmit={handleUpload} className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label className="yc-label">Video *</label>
            <select required className="yc-select" value={form.video_id} onChange={(e) => setForm({ ...form, video_id: e.target.value })}>
              <option value="">Select ready video</option>
              {videos.map((v) => <option key={v.id} value={v.id}>{v.title} ({v.status})</option>)}
            </select>
          </div>
          <div>
            <label className="yc-label">Visibility</label>
            <select className="yc-select" value={form.visibility} onChange={(e) => setForm({ ...form, visibility: e.target.value })}>
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>
          {form.visibility === 'public' && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--warn)' }}>
              <input type="checkbox" checked={form.approve} onChange={(e) => setForm({ ...form, approve: e.target.checked })} />
              I approve publishing this video publicly
            </label>
          )}
          {error && <p style={{ color: 'var(--danger)', fontSize: 13, margin: 0 }}>{error}</p>}
          {success && <p style={{ color: 'var(--success)', fontSize: 13, margin: 0 }}>{success}</p>}
          <button type="submit" disabled={loading || !channel} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
            {loading ? 'Uploading…' : 'Upload to YouTube'}
          </button>
        </form>

        <div className="yc-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.85rem', fontSize: 14, fontWeight: 600 }}>Upload History</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 360, overflowY: 'auto' }}>
            {uploads.map((u) => (
              <div key={u.id} className="yc-card" style={{ padding: '0.75rem 0.9rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 13 }}>Video #{u.video_id}</span>
                  <span style={{ fontSize: 11, color: u.status === 'uploaded' ? 'var(--success)' : 'var(--warn)' }}>{u.status}</span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: 11, color: 'var(--text-dim)' }}>
                  {u.visibility} · {new Date(u.created_at).toLocaleString()}
                </p>
                {u.youtube_url && (
                  <a href={u.youtube_url} target="_blank" rel="noreferrer"
                    style={{ fontSize: 12, color: 'var(--accent)', display: 'inline-flex', alignItems: 'center', gap: 4, marginTop: 4 }}>
                    Open on YouTube <ExternalLink size={11} />
                  </a>
                )}
              </div>
            ))}
            {uploads.length === 0 && <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No uploads yet.</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
