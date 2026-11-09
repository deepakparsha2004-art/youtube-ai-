import { useState, useEffect } from 'react'
import { createSchedule, listSchedules, toggleSchedule, deleteSchedule } from '../services/api'
import { Settings, Plus, Trash2 } from 'lucide-react'

export default function AutomationSettings() {
  const [schedules, setSchedules] = useState([])
  const [form, setForm] = useState({
    name: '', topic_template: '', script_type: 'general', is_short: false,
    cron_expression: '0 9 * * *', is_active: true,
  })
  const load = () => listSchedules().then((r) => setSchedules(r.data)).catch(console.error)
  useEffect(() => { load() }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Settings size={24} color="var(--accent)" /> Automation</h1>
        <p className="yc-page-sub">Schedule recurring video creation (cron-based)</p>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
        <form onSubmit={async (e) => {
          e.preventDefault()
          await createSchedule(form)
          setForm({ ...form, name: '', topic_template: '' })
          load()
        }} className="yc-panel" style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input required className="yc-input" placeholder="Schedule name" value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="yc-input" placeholder="Topic template (optional)" value={form.topic_template}
            onChange={(e) => setForm({ ...form, topic_template: e.target.value })} />
          <input className="yc-input" placeholder="Cron e.g. 0 9 * * *" value={form.cron_expression}
            onChange={(e) => setForm({ ...form, cron_expression: e.target.value })} />
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <input type="checkbox" checked={form.is_short} onChange={(e) => setForm({ ...form, is_short: e.target.checked })} />
            YouTube Shorts
          </label>
          <button type="submit" className="yc-btn yc-btn-primary" style={{ width: '100%' }}>
            <Plus size={18} /> Create Schedule
          </button>
        </form>
        <div className="yc-panel" style={{ padding: '1.25rem' }}>
          <h3 style={{ margin: '0 0 0.85rem', fontSize: 14, fontWeight: 600 }}>Schedules</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {schedules.map((s) => (
              <div key={s.id} className="yc-card" style={{ padding: '0.75rem 0.9rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>{s.name}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{s.cron_expression} · {s.is_active ? 'Active' : 'Paused'}</div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <button className="yc-btn yc-btn-ghost" style={{ fontSize: 11, padding: '4px 8px' }}
                    onClick={() => toggleSchedule(s.id, !s.is_active).then(load)}>
                    {s.is_active ? 'Pause' : 'Resume'}
                  </button>
                  <button className="yc-btn yc-btn-ghost" style={{ padding: 6 }} onClick={() => deleteSchedule(s.id).then(load)}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
            {schedules.length === 0 && <p style={{ color: 'var(--text-dim)', fontSize: 13 }}>No schedules yet.</p>}
          </div>
        </div>
      </div>
    </div>
  )
}
