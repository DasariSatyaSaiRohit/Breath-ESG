import React, { createContext, useContext, useState, useRef, useCallback } from 'react'
import type { ReactNode } from 'react'
import { AuthState, AuthUser } from '../types'
import { loginApi } from '../api/auth'

interface AuthContextValue {
  auth: AuthState
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setAccessToken: (token: string) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

// Module-level ref so axios interceptor can access token without circular deps
export const accessTokenRef = { current: null as string | null }

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ accessToken: null, user: null })

  const login = useCallback(async (email: string, password: string) => {
    const data = await loginApi(email, password)
    accessTokenRef.current = data.access_token
    setAuth({ accessToken: data.access_token, user: data.user })
  }, [])

  const logout = useCallback(() => {
    accessTokenRef.current = null
    setAuth({ accessToken: null, user: null })
    // Optionally call logout endpoint — fire-and-forget
    fetch('/api/auth/logout/', { method: 'POST' }).catch(() => {})
  }, [])

  const setAccessToken = useCallback((token: string) => {
    accessTokenRef.current = token
    setAuth(prev => ({ ...prev, accessToken: token }))
  }, [])

  return (
    <AuthContext.Provider value={{ auth, login, logout, setAccessToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
