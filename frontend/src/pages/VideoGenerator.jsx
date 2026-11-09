import { useState, useEffect } from 'react'
import { createVideo, generateFalVideo, listVideos, listScripts, deleteVideo, getVideoFile } from '../services/api'
import { Video, Loader2, Trash2, Film } from 'lucide-react'

export default function VideoGenerator() {
  const [scripts, setScripts] = useState([])
  const [videos, setVideos] = useState([])
  const [form, setForm] = useState({
    script_id: '', is_short: false, voice: 'en-US-AriaNeural', add_subtitles: true, pexels_query: '',
  })
  const [mode, setMode] = useState('script')
  const [falForm, setFalForm] = useState({
    prompt: '', title: '', is_short: false, duration: '8s', generate_audio: false,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [videoUrl, setVideoUrl] = useState('')

  useEffect(() => {
    let active = true
    let objectUrl
    setVideoUrl('')
    if (selected?.video_path) {
      getVideoFile(selected.id)
        .then(({ data }) => {
          objectUrl = URL.createObjectURL(data)
          if (active) setVideoUrl(objectUrl)
          else URL.revokeObjectURL(objectUrl)
        })
        .catch((err) => setError(err.response?.data?.detail || 'Could not load generated video'))
    }
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [selected?.id, selected?.video_path])

  const load = () => {
    listScripts().then((r) => setScripts(r.data)).catch(console.error)
    listVideos().then((r) => setVideos(r.data)).catch(console.error)
  }
  useEffect(() => { load() }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!form.script_id) return
    setLoading(true)
    setError('')
    try {
      const res = await createVideo({
        ...form, script_id: Number(form.script_id), pexels_query: form.pexels_query || undefined,
      })
      setSelected(res.data)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Video creation failed. Check MoviePy/ffmpeg and Pexels key.')
    } finally {
      setLoading(false)
    }
  }

  const handleFalCreate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await generateFalVideo({
        ...falForm,
        title: falForm.title || undefined,
      })
      setSelected(res.data)
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'fal.ai video generation failed.')
      load()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Video size={24} color="var(--accent)" /> Video Generator</h1>
        <p className="yc-page-sub">Create videos from scripts or generate clips with fal.ai</p>
      </div>

      <div className="yc-workspace-grid">
        <div className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 14, height: 'fit-content' }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="button" className={`yc-btn ${mode === 'script' ? 'yc-btn-primary' : 'yc-btn-ghost'}`} onClick={() => setMode('script')}>
              Script video
            </button>
            <button type="button" className={`yc-btn ${mode === 'fal' ? 'yc-btn-primary' : 'yc-btn-ghost'}`} onClick={() => setMode('fal')}>
              fal.ai video
            </button>
          </div>
          {mode === 'script' ? (
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label className="yc-label">Script *</label>
                <select required className="yc-select" value={form.script_id} onChange={(e) => setForm({ ...form, script_id: e.target.value })}>
                  <option value="">Select a script</option>
                  {scripts.map((s) => <option key={s.id} value={s.id}>{s.title || s.topic}</option>)}
                </select>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
                <input type="checkbox" checked={form.is_short} onChange={(e) => setForm({ ...form, is_short: e.target.checked })} />
                YouTube Shorts (9:16)
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
                <input type="checkbox" checked={form.add_subtitles} onChange={(e) => setForm({ ...form, add_subtitles: e.target.checked })} />
                Add title overlay
              </label>
              <div>
                <label className="yc-label">Pexels query (optional)</label>
                <input className="yc-input" placeholder="technology abstract" value={form.pexels_query}
                  onChange={(e) => setForm({ ...form, pexels_query: e.target.value })} />
              </div>
              <div>
                <label className="yc-label">Voice</label>
                <input className="yc-input" value={form.voice} onChange={(e) => setForm({ ...form, voice: e.target.value })} />
              </div>
              {error && <p style={{ color: 'var(--danger)', fontSize: 13, margin: 0 }}>{error}</p>}
              <button type="submit" disabled={loading} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Film size={18} />}
                {loading ? 'Rendering…' : 'Create Video'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleFalCreate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label className="yc-label">Video prompt *</label>
                <textarea required minLength={3} maxLength={2000} rows={5} className="yc-input"
                  placeholder="Describe the subject, setting, action, visual style, and camera movement"
                  value={falForm.prompt}
                  onChange={(e) => setFalForm({ ...falForm, prompt: e.target.value })} />
              </div>
              <div>
                <label className="yc-label">Title (optional)</label>
                <input maxLength={200} className="yc-input" value={falForm.title}
                  onChange={(e) => setFalForm({ ...falForm, title: e.target.value })} />
              </div>
              <div>
                <label className="yc-label">Clip length</label>
                <select className="yc-select" value={falForm.duration}
                  onChange={(e) => setFalForm({ ...falForm, duration: e.target.value })}>
                  <option value="4s">4 seconds</option>
                  <option value="6s">6 seconds</option>
                  <option value="8s">8 seconds</option>
                </select>
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
                <input type="checkbox" checked={falForm.is_short}
                  onChange={(e) => setFalForm({ ...falForm, is_short: e.target.checked })} />
                Vertical video (9:16)
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
                <input type="checkbox" checked={falForm.generate_audio}
                  onChange={(e) => setFalForm({ ...falForm, generate_audio: e.target.checked })} />
                Generate model audio (may cost more)
              </label>
              <p style={{ margin: 0, fontSize: 11, color: 'var(--text-dim)' }}>
                Uses fal.ai Veo 3.1 Fast at 720p. Generation is billed by fal.ai; review its current pricing before submitting.
              </p>
              {error && <p style={{ color: 'var(--danger)', fontSize: 13, margin: 0 }}>{error}</p>}
              <button type="submit" disabled={loading} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Film size={18} />}
                {loading ? 'Generating with fal.ai…' : 'Generate AI Video'}
              </button>
            </form>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {selected && (
            <div className="yc-panel yc-animate" style={{ padding: '1.25rem' }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{selected.title}</h3>
              <p style={{ margin: '4px 0 12px', fontSize: 12, color: 'var(--text-dim)' }}>
                Status: <span style={{ color: 'var(--accent)' }}>{selected.status}</span> · {selected.duration_seconds}s · {selected.width}×{selected.height}
              </p>
              {selected.video_path && (
                videoUrl && (
                  <video controls style={{ width: '100%', borderRadius: 12, maxHeight: 320, background: '#000' }}
                    src={videoUrl} />
                )
              )}
              {selected.error_message && <p style={{ color: 'var(--danger)', fontSize: 13 }}>{selected.error_message}</p>}
            </div>
          )}

          <div className="yc-panel" style={{ padding: '1.25rem' }}>
            <h3 style={{ margin: '0 0 0.85rem', fontSize: 14, fontWeight: 600 }}>Generated Videos</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 280, overflowY: 'auto' }}>
              {videos.map((v) => (
                <div key={v.id} onClick={() => setSelected(v)} className="yc-card"
                  style={{ padding: '0.7rem 0.9rem', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{v.title}</div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{v.status} · {v.is_short ? 'Short' : 'Long'}</div>
                  </div>
                  <button className="yc-btn yc-btn-ghost" style={{ padding: 6 }}
                    onClick={(e) => { e.stopPropagation(); deleteVideo(v.id).then(load) }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {videos.length === 0 && <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No videos yet.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
