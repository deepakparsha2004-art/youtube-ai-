import { useEffect, useState } from 'react'
import { getSystemStatus } from '../services/api'
import { Key, CheckCircle, XCircle } from 'lucide-react'

export default function APISettings() {
  const [status, setStatus] = useState(null)
  useEffect(() => {
    getSystemStatus().then((r) => setStatus(r.data)).catch(console.error)
  }, [])

  const Row = ({ label, ok, detail }) => (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '0.85rem 0', borderBottom: '1px solid rgba(30,41,59,0.6)'
    }}>
      <div>
        <div style={{ fontSize: 14, color: '#fff' }}>{label}</div>
        {detail && <div style={{ fontSize: 11, color: 'var(--text-dim)', marginTop: 2 }}>{detail}</div>}
      </div>
      {ok ? <CheckCircle color="var(--success)" size={20} /> : <XCircle color="var(--danger)" size={20} />}
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h1 className="yc-page-title"><Key size={24} color="var(--accent)" /> API Settings</h1>
        <p className="yc-page-sub">System integration status (keys live in backend .env)</p>
      </div>

      <div className="yc-panel" style={{ padding: '1.25rem', maxWidth: 480 }}>
        {!status ? (
          <p style={{ color: 'var(--text-dim)' }}>Loading…</p>
        ) : (
          <>
            <Row label="Ollama LLM" ok={status.ollama_available} detail={`Model: ${status.ollama_model}`} />
            <Row label="fal.ai Video" ok={status.fal_video_configured} detail={`Model: ${status.fal_video_model} · Configure a rotated FAL_KEY and set FAL_VIDEO_ENABLED=true in backend/.env, then restart`} />
            <Row label="Pexels Stock Footage" ok={status.pexels_configured} detail="Set PEXELS_API_KEY in backend/.env" />
            <Row label="Google OAuth / YouTube" ok={status.google_oauth_configured} detail="Set GOOGLE_CLIENT_ID & SECRET" />
            <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 14 }}>App version: {status.app_version}</p>
            {status.available_models?.length > 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-dim)' }}>Models: {status.available_models.join(', ')}</p>
            )}
          </>
        )}
      </div>

      <div className="yc-panel" style={{ padding: '1.25rem', maxWidth: 480, fontSize: 13, color: 'var(--text-dim)' }}>
        <p style={{ fontWeight: 600, color: '#fff', marginTop: 0 }}>How to configure</p>
        <ol style={{ paddingLeft: 18, lineHeight: 1.7, margin: 0 }}>
          <li>Copy backend/.env.example → backend/.env</li>
          <li>Pexels key: https://www.pexels.com/api/</li>
          <li>Google Cloud → enable YouTube Data API v3 → OAuth client</li>
          <li>Redirect URI: http://localhost:8000/api/v1/youtube/oauth/callback</li>
          <li>ollama pull llama3.2</li>
        </ol>
      </div>
    </div>
  )
}
