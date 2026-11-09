import { createContext, useContext, useEffect, useState } from 'react'
import api, { TOKEN_KEY } from '../services/api'

const AUTH_REQUIRED = import.meta.env.VITE_AUTH_REQUIRED === 'true'
const guestUser = { username: 'Local workspace', email: 'Sign-in not required', full_name: 'Local workspace' }

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(AUTH_REQUIRED ? null : guestUser)
  const [loading, setLoading] = useState(AUTH_REQUIRED)
  const [oauthError, setOauthError] = useState('')

  useEffect(() => {
    if (!AUTH_REQUIRED) return undefined

    const handleUnauthorized = () => setUser(null)
    window.addEventListener('auth:unauthorized', handleUnauthorized)

    const callbackParams = new URLSearchParams(window.location.hash.slice(1))
    const callbackToken = callbackParams.get('oauth_token')
    const callbackError = callbackParams.get('oauth_error')
    if (callbackToken || callbackError) {
      window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}`)
    }
    if (callbackError) {
      const messages = {
        invalid_state: 'Sign-in expired or could not be verified. Please try again.',
        sign_in_cancelled: 'Sign-in was cancelled.',
        provider_not_configured: 'This sign-in option has not been configured yet.',
        account_unavailable: 'This account is inactive or cannot be created.',
        sign_in_failed: 'Sign-in failed. Please try again.',
      }
      setOauthError(messages[callbackError] || 'Sign-in failed. Please try again.')
    }

    const token = callbackToken || window.sessionStorage.getItem(TOKEN_KEY)
    if (callbackToken) window.sessionStorage.setItem(TOKEN_KEY, callbackToken)
    if (!token) {
      setLoading(false)
      return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
    }

    api.get('/auth/me')
      .then((response) => setUser(response.data))
      .catch(() => {
        window.sessionStorage.removeItem(TOKEN_KEY)
        setUser(null)
        if (callbackToken) setOauthError('Sign-in could not be verified. Please try again.')
      })
      .finally(() => setLoading(false))

    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  const login = async (username, password) => {
    const form = new URLSearchParams({ username, password })
    const response = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    window.sessionStorage.setItem(TOKEN_KEY, response.data.access_token)
    setUser(response.data.user)
  }

  const logout = () => {
    window.sessionStorage.removeItem(TOKEN_KEY)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, oauthError, authRequired: AUTH_REQUIRED }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
