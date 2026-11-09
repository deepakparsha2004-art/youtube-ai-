import { useAuth } from '../context/AuthContext'
import { User } from 'lucide-react'

export default function UserProfile() {
  const { user } = useAuth()
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><User size={24} color="var(--accent)" /> Profile</h1>
      </div>
      <div className="yc-panel" style={{ padding: '1.75rem', maxWidth: 400 }}>
        <div style={{
          width: 64, height: 64, borderRadius: 16, marginBottom: 16,
          background: 'linear-gradient(135deg, rgba(34,211,238,0.3), rgba(129,140,248,0.3))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 24, fontWeight: 800, color: 'var(--accent)'
        }}>
          {user?.username?.[0]?.toUpperCase()}
        </div>
        {[
          ['Username', user?.username],
          ['Email', user?.email],
          ['Full name', user?.full_name || '—'],
          ['Member since', user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'],
        ].map(([label, val]) => (
          <div key={label} style={{ marginBottom: 14 }}>
            <div className="yc-label">{label}</div>
            <div style={{ fontSize: 14, color: '#fff' }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
