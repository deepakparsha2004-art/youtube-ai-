import { useState, useEffect } from 'react'
import { listVideos, createThumbnail, getThumbnailFile } from '../services/api'
import { Image, Loader2 } from 'lucide-react'

export default function ThumbnailGenerator() {
  const [videos, setVideos] = useState([])
  const [videoId, setVideoId] = useState('')
  const [title, setTitle] = useState('')
  const [style, setStyle] = useState('modern')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [thumbnailUrl, setThumbnailUrl] = useState('')

  useEffect(() => { listVideos().then((r) => setVideos(r.data)).catch(console.error) }, [])

  useEffect(() => {
    let active = true
    let objectUrl
    setThumbnailUrl('')
    if (result?.thumbnail_path) {
      getThumbnailFile(result.id)
        .then(({ data }) => {
          objectUrl = URL.createObjectURL(data)
          if (active) setThumbnailUrl(objectUrl)
          else URL.revokeObjectURL(objectUrl)
        })
        .catch(console.error)
    }
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [result?.id, result?.thumbnail_path])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Image size={24} color="var(--accent)" /> Thumbnail Generator</h1>
        <p className="yc-page-sub">Create eye-catching thumbnails in Command Center style</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        <form onSubmit={async (e) => {
          e.preventDefault()
          setLoading(true)
          try {
            const res = await createThumbnail(Number(videoId), { video_id: Number(videoId), title: title || undefined, style })
            setResult(res.data)
          } catch (err) {
            alert(err.response?.data?.detail || 'Failed')
          } finally {
            setLoading(false)
          }
        }} className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div>
            <label className="yc-label">Video</label>
            <select required className="yc-select" value={videoId} onChange={(e) => setVideoId(e.target.value)}>
              <option value="">Select video</option>
              {videos.map((v) => <option key={v.id} value={v.id}>{v.title}</option>)}
            </select>
          </div>
          <div>
            <label className="yc-label">Custom title</label>
            <input className="yc-input" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          <div>
            <label className="yc-label">Style</label>
            <select className="yc-select" value={style} onChange={(e) => setStyle(e.target.value)}>
              <option value="modern">Modern</option>
              <option value="bold">Bold</option>
              <option value="minimal">Minimal</option>
              <option value="tech">Tech</option>
            </select>
          </div>
          <button type="submit" disabled={loading} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Image size={18} />}
            Generate Thumbnail
          </button>
        </form>
        <div className="yc-panel" style={{ padding: '1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 220 }}>
          {thumbnailUrl ? (
            <img src={thumbnailUrl} alt="Thumbnail"
              style={{ maxWidth: '100%', borderRadius: 12, boxShadow: '0 8px 32px rgba(0,0,0,0.4)' }} />
          ) : (
            <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>Thumbnail preview appears here</p>
          )}
        </div>
      </div>
    </div>
  )
}
