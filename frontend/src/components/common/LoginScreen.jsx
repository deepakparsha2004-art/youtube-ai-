import { useState } from 'react'
import { LogIn, Loader2, Sparkles } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'

export default function LoginScreen() {
  const { login, oauthError } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      await login(username, password)
    } catch (loginError) {
      setError(loginError.response?.data?.detail || 'Sign in failed. Check your username and password.')
    } finally {
      setSubmitting(false)
    }
  }

  const startOAuth = (provider) => {
    const baseURL = api.defaults.baseURL || '/api/v1'
    const loginURL = new URL(`${baseURL.replace(/\/$/, '')}/auth/${provider}`, window.location.origin)
    window.location.assign(loginURL)
  }

  return (
    <main style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: 24 }}>
      <form onSubmit={handleSubmit} className="yc-panel" style={{ width: '100%', maxWidth: 400, padding: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <Sparkles size={26} color="var(--accent)" />
          <div>
            <h1 style={{ margin: 0, fontSize: 20 }}>Sign in</h1>
            <p className="yc-page-sub" style={{ margin: '4px 0 0' }}>YouTube AI Command Center</p>
          </div>
        </div>
        <button
          type="button"
          className="yc-btn yc-btn-ghost"
          onClick={() => startOAuth('google')}
          style={{ width: '100%', marginBottom: 10, justifyContent: 'center' }}
        >
          Continue with Google
        </button>
        <button
          type="button"
          className="yc-btn yc-btn-ghost"
          onClick={() => startOAuth('github')}
          style={{ width: '100%', marginBottom: 16, justifyContent: 'center' }}
        >
          Continue with GitHub
        </button>
        <div aria-hidden="true" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
          <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span className="yc-page-sub" style={{ fontSize: 12 }}>or use your password</span>
          <span style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>
        <label className="yc-label" htmlFor="username">Username</label>
        <input
          id="username"
          className="yc-input"
          autoComplete="username"
          required
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          style={{ width: '100%', marginBottom: 16 }}
        />
        <label className="yc-label" htmlFor="password">Password</label>
        <input
          id="password"
          className="yc-input"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          style={{ width: '100%', marginBottom: 16 }}
        />
        {(error || oauthError) && (
          <p role="alert" style={{ color: 'var(--danger)', fontSize: 13 }}>{error || oauthError}</p>
        )}
        <button type="submit" className="yc-btn yc-btn-primary" disabled={submitting} style={{ width: '100%' }}>
          {submitting ? <Loader2 className="animate-spin" size={18} /> : <LogIn size={18} />}
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </main>
  )
}
