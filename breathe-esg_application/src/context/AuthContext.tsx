import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import type { ReactNode } from 'react'
import { AuthState, AuthUser, TenantConfig } from '../types'
import { loginApi } from '../api/auth'
import axiosInstance from '../api/axios'

interface AuthContextValue {
  auth: AuthState
  tenantConfig: TenantConfig | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  setAccessToken: (token: string) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

// Module-level ref so axios interceptor can access token without circular deps
export const accessTokenRef = { current: null as string | null }

async function fetchTenantConfig(): Promise<TenantConfig> {
  const { data } = await axiosInstance.get('tenant/config/')
  return data
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [auth, setAuth] = useState<AuthState>({ accessToken: null, user: null })
  const [tenantConfig, setTenantConfig] = useState<TenantConfig | null>(null)

  // Fetch tenant config once we have a token
  useEffect(() => {
    if (auth.accessToken) {
      fetchTenantConfig()
        .then(setTenantConfig)
        .catch(() => {
          // Fallback config if endpoint not yet available
          setTenantConfig({
            id: 0,
            name: auth.user?.tenant_name ?? '',
            timezone: 'UTC',
            date_display_format: 'YYYY-MM-DD',
          })
        })
    } else {
      setTenantConfig(null)
    }
  }, [auth.accessToken, auth.user?.tenant_name])

  const login = useCallback(async (email: string, password: string) => {
    const data = await loginApi(email, password)
    accessTokenRef.current = data.access_token
    setAuth({ accessToken: data.access_token, user: data.user })
  }, [])

  const logout = useCallback(() => {
    accessTokenRef.current = null
    setAuth({ accessToken: null, user: null })
    setTenantConfig(null)
    fetch('/api/auth/logout/', { method: 'POST' }).catch(() => {})
  }, [])

  const setAccessToken = useCallback((token: string) => {
    accessTokenRef.current = token
    setAuth(prev => ({ ...prev, accessToken: token }))
  }, [])

  return (
    <AuthContext.Provider value={{ auth, tenantConfig, login, logout, setAccessToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
