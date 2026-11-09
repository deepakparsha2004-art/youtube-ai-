import { useEffect, useState } from 'react'
import { getLogs } from '../services/api'
import { History } from 'lucide-react'

export default function HistoryLogs() {
  const [logs, setLogs] = useState([])
  useEffect(() => { getLogs().then((r) => setLogs(r.data)).catch(console.error) }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><History size={24} color="var(--accent)" /> History & Logs</h1>
        <p className="yc-page-sub">Activity audit trail</p>
      </div>
      <div className="yc-panel" style={{ overflow: 'hidden' }}>
        <table className="yc-table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Entity</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td style={{ color: '#e2e8f0' }}>{log.action.replace(/_/g, ' ')}</td>
                <td style={{ color: 'var(--text-dim)' }}>{log.entity_type} {log.entity_id ? `#${log.entity_id}` : ''}</td>
                <td style={{ color: 'var(--text-dim)' }}>{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {logs.length === 0 && <p className="yc-empty" style={{ padding: '2rem' }}>No logs yet.</p>}
      </div>
    </div>
  )
}
