import { createContext, useContext } from 'react'

const workspaceUser = { username: 'Local workspace', email: 'Sign-in not required', full_name: 'Local workspace' }

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  return (
    <AuthContext.Provider value={{ user: workspaceUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
