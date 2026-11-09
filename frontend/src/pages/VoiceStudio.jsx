import { useState, useEffect } from 'react'
import { recommendedVoices, generateVoice, listScripts, getAudioFile } from '../services/api'
import { Mic, Play, Loader2 } from 'lucide-react'

export default function VoiceStudio() {
  const [voices, setVoices] = useState([])
  const [scripts, setScripts] = useState([])
  const [form, setForm] = useState({ text: '', voice: 'en-US-AriaNeural', rate: '+0%', pitch: '+0Hz', script_id: null })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [audioUrl, setAudioUrl] = useState('')

  useEffect(() => {
    let active = true
    let objectUrl
    setAudioUrl('')
    if (result?.filename) {
      getAudioFile(result.filename)
        .then(({ data }) => {
          objectUrl = URL.createObjectURL(data)
          if (active) setAudioUrl(objectUrl)
          else URL.revokeObjectURL(objectUrl)
        })
        .catch((err) => setError(err.response?.data?.detail || 'Could not load generated audio'))
    }
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [result?.filename])

  useEffect(() => {
    recommendedVoices().then((r) => setVoices(r.data)).catch(console.error)
    listScripts().then((r) => setScripts(r.data)).catch(console.error)
  }, [])

  const handleGenerate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const payload = { ...form }
      if (form.script_id) payload.script_id = Number(form.script_id)
      else delete payload.script_id
      const res = await generateVoice(payload)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Voice generation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Mic size={24} color="var(--accent)" /> Voice Studio</h1>
        <p className="yc-page-sub">Convert scripts to natural AI speech with Edge TTS</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        <form onSubmit={handleGenerate} className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label className="yc-label">Use existing script</label>
            <select className="yc-select" value={form.script_id || ''} onChange={(e) => setForm({ ...form, script_id: e.target.value || null })}>
              <option value="">— Type custom text —</option>
              {scripts.map((s) => <option key={s.id} value={s.id}>{s.title || s.topic}</option>)}
            </select>
          </div>
          {!form.script_id && (
            <div>
              <label className="yc-label">Text to speak</label>
              <textarea rows={5} required={!form.script_id} className="yc-textarea"
                value={form.text} onChange={(e) => setForm({ ...form, text: e.target.value })} />
            </div>
          )}
          <div>
            <label className="yc-label">Voice</label>
            <select className="yc-select" value={form.voice} onChange={(e) => setForm({ ...form, voice: e.target.value })}>
              {voices.map((v) => (
                <option key={v.short_name} value={v.short_name}>{v.name} ({v.gender})</option>
              ))}
            </select>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label className="yc-label">Rate</label>
              <input className="yc-input" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} />
            </div>
            <div>
              <label className="yc-label">Pitch</label>
              <input className="yc-input" value={form.pitch} onChange={(e) => setForm({ ...form, pitch: e.target.value })} />
            </div>
          </div>
          {error && <p style={{ color: 'var(--danger)', fontSize: 13, margin: 0 }}>{error}</p>}
          <button type="submit" disabled={loading} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Mic size={18} />}
            {loading ? 'Generating…' : 'Generate Voice'}
          </button>
        </form>

        <div className="yc-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 1rem', fontSize: 14, fontWeight: 600 }}>Preview</h3>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-dim)' }}>Voice: <strong style={{ color: '#fff' }}>{result.voice}</strong></p>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-dim)' }}>Duration: ~{result.duration_seconds}s</p>
              {audioUrl && <audio controls style={{ width: '100%' }} src={audioUrl} />}
              <p style={{ margin: 0, fontSize: 11, color: 'var(--text-dim)', wordBreak: 'break-all' }}>{result.filename}</p>
            </div>
          ) : (
            <div className="yc-empty">
              <Play size={40} style={{ opacity: 0.35, marginBottom: 8 }} />
              <p style={{ margin: 0, fontSize: 13 }}>Generate a voiceover to preview</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
