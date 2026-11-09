import { useEffect, useState } from 'react'
import { researchTopics } from '../services/api'
import { Calendar, RefreshCw } from 'lucide-react'

export default function ContentCalendar() {
  const [niche, setNiche] = useState('technology')
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    researchTopics(niche).then((r) => setTopics(r.data.suggestions || [])).catch(console.error).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
        <div>
          <h1 className="yc-page-title"><Calendar size={24} color="var(--accent)" /> Content Ideas</h1>
          <p className="yc-page-sub">AI-suggested topics for your content plan</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <input className="yc-input" style={{ width: 160 }} value={niche} onChange={(e) => setNiche(e.target.value)} placeholder="Niche" />
          <button className="yc-btn yc-btn-ghost" onClick={load} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '1rem' }}>
        {topics.map((t, i) => (
          <div key={i} className="yc-card yc-animate" style={{ padding: '1.1rem' }}>
            <span className="yc-chip">{t.estimated_interest}</span>
            <h3 style={{ margin: '8px 0 6px', fontSize: 14, fontWeight: 700, color: '#fff' }}>{t.topic}</h3>
            <p style={{ margin: 0, fontSize: 12, color: 'var(--text-dim)', lineHeight: 1.45 }}>{t.reason}</p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 10 }}>
              {(t.keywords || []).map((k) => (
                <span key={k} style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: 'rgba(30,41,59,0.8)', color: 'var(--text-dim)' }}>{k}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
