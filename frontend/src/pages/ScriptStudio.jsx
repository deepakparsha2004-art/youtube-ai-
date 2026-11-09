import { useState, useEffect } from 'react'
import { generateScript, listScripts, deleteScript } from '../services/api'
import { FileText, Sparkles, Trash2, Loader2, Copy, Check } from 'lucide-react'

export default function ScriptStudio() {
  const [form, setForm] = useState({
    topic: '', script_type: 'general', length: 'medium', tone: 'engaging',
    include_hooks: true, generate_title: true, generate_description: true, generate_hashtags: true,
  })
  const [scripts, setScripts] = useState([])
  const [selected, setSelected] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  const load = () => listScripts().then((r) => setScripts(r.data)).catch(console.error)
  useEffect(() => { load() }, [])

  const handleGenerate = async (e) => {
    e.preventDefault()
    if (!form.topic.trim()) return
    setLoading(true)
    setError('')
    try {
      const res = await generateScript(form)
      setSelected(res.data)
      load()
    } catch (err) {
      const detail = err.response?.data?.detail
      setError(
        typeof detail === 'string'
          ? detail
          : err.response
            ? 'Script generation failed. Check the backend logs and try again.'
            : 'Could not reach the backend. Check that the backend server is running, then try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this script?')) return
    await deleteScript(id)
    if (selected?.id === id) setSelected(null)
    load()
  }

  const copyText = () => {
    if (!selected) return
    navigator.clipboard.writeText(selected.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><FileText size={24} color="var(--accent)" /> Script Studio</h1>
        <p className="yc-page-sub">Generate engaging YouTube scripts with local Ollama LLM</p>
      </div>

      <div className="yc-workspace-grid">
        <form onSubmit={handleGenerate} className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 14, height: 'fit-content' }}>
          <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: '#fff' }}>New Script</h3>
          <div>
            <label className="yc-label">Topic *</label>
            <textarea rows={3} required className="yc-textarea" placeholder="e.g. How AI is changing content creation"
              value={form.topic} onChange={(e) => setForm({ ...form, topic: e.target.value })} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            <div>
              <label className="yc-label">Type</label>
              <select className="yc-select" value={form.script_type} onChange={(e) => setForm({ ...form, script_type: e.target.value })}>
                <option value="general">General</option>
                <option value="educational">Educational</option>
                <option value="motivational">Motivational</option>
                <option value="technology">Technology</option>
                <option value="short">Short-form</option>
                <option value="long">Long-form</option>
              </select>
            </div>
            <div>
              <label className="yc-label">Length</label>
              <select className="yc-select" value={form.length} onChange={(e) => setForm({ ...form, length: e.target.value })}>
                <option value="short">Short (~1 min)</option>
                <option value="medium">Medium (3-6 min)</option>
                <option value="long">Long (8-15 min)</option>
              </select>
            </div>
          </div>
          <div>
            <label className="yc-label">Tone</label>
            <input className="yc-input" value={form.tone} onChange={(e) => setForm({ ...form, tone: e.target.value })} />
          </div>
          {error && <p style={{ color: 'var(--danger)', fontSize: 13, margin: 0 }}>{error}</p>}
          <button type="submit" disabled={loading} className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
            {loading ? <Loader2 className="animate-spin" size={18} /> : <Sparkles size={18} />}
            {loading ? 'Generating…' : 'Generate Script'}
          </button>
        </form>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {selected && (
            <div className="yc-panel yc-animate" style={{ padding: '1.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 12 }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: '#fff' }}>{selected.title}</h3>
                  <p style={{ margin: '4px 0 0', fontSize: 12, color: 'var(--text-dim)' }}>
                    {selected.word_count} words · ~{Math.round(selected.estimated_duration_seconds / 60)} min · {selected.script_type}
                  </p>
                </div>
                <button className="yc-btn yc-btn-ghost" style={{ padding: '0.4rem 0.6rem' }} onClick={copyText}>
                  {copied ? <Check size={16} /> : <Copy size={16} />}
                </button>
              </div>
              {selected.description && (
                <p style={{ fontSize: 13, color: 'var(--text-dim)', background: 'rgba(3,7,18,0.5)', padding: '0.75rem', borderRadius: 10, marginBottom: 12 }}>
                  {selected.description}
                </p>
              )}
              <div style={{
                maxHeight: 280, overflowY: 'auto', fontSize: 13, lineHeight: 1.65, color: '#e2e8f0',
                whiteSpace: 'pre-wrap', background: 'rgba(3,7,18,0.45)', padding: '1rem', borderRadius: 10,
                border: '1px solid var(--border-dim)'
              }}>
                {selected.content}
              </div>
              {selected.hashtags?.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
                  {selected.hashtags.map((h) => <span key={h} className="yc-chip">{h}</span>)}
                </div>
              )}
            </div>
          )}

          <div className="yc-panel" style={{ padding: '1.25rem' }}>
            <h3 style={{ margin: '0 0 0.85rem', fontSize: 14, fontWeight: 600 }}>Your Scripts ({scripts.length})</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 260, overflowY: 'auto' }}>
              {scripts.map((s) => (
                <div
                  key={s.id}
                  onClick={() => setSelected(s)}
                  className="yc-card"
                  style={{
                    padding: '0.7rem 0.9rem', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    borderColor: selected?.id === s.id ? 'var(--border-glow)' : undefined,
                    background: selected?.id === s.id ? 'rgba(34,211,238,0.08)' : undefined,
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.title || s.topic}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{new Date(s.created_at).toLocaleString()}</div>
                  </div>
                  <button className="yc-btn yc-btn-ghost" style={{ padding: 6 }} onClick={(e) => { e.stopPropagation(); handleDelete(s.id) }}>
                    <Trash2 size={14} />
                  </button>
                </div>
              ))}
              {scripts.length === 0 && <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No scripts yet.</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
