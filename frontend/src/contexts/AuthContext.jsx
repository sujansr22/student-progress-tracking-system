import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react'
import { authApi, setAuthToken } from '../api/client'

const AuthContext = createContext(null)

function parseJwt(token) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(null)
  const [refreshToken, setRefreshToken] = useState(null)
  const [user, setUser] = useState(null)  // decoded JWT payload
  const [loading, setLoading] = useState(false)
  const refreshTimerRef = useRef(null)

  const scheduleRefresh = useCallback((token, refresh) => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    const payload = parseJwt(token)
    if (!payload?.exp) return
    // Refresh 60 seconds before expiry
    const msUntilRefresh = (payload.exp * 1000) - Date.now() - 60_000
    if (msUntilRefresh <= 0) return
    refreshTimerRef.current = setTimeout(async () => {
      try {
        const { data } = await authApi.refresh(refresh)
        applyTokens(data.access_token, data.refresh_token)
      } catch {
        logout()
      }
    }, msUntilRefresh)
  }, [])

  function applyTokens(access, refresh) {
    setAccessToken(access)
    setRefreshToken(refresh)
    setAuthToken(access)
    const payload = parseJwt(access)
    setUser(payload)
    scheduleRefresh(access, refresh)
  }

  async function login(email, password) {
    setLoading(true)
    try {
      const { data } = await authApi.login(email, password)
      applyTokens(data.access_token, data.refresh_token)
      return { ok: true }
    } catch (err) {
      return { ok: false, message: err.response?.data?.detail || 'Login failed' }
    } finally {
      setLoading(false)
    }
  }

  async function logout() {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    if (refreshToken) {
      authApi.logout(refreshToken).catch(() => {})
    }
    setAccessToken(null)
    setRefreshToken(null)
    setUser(null)
    setAuthToken(null)
  }

  const isAuthenticated = !!accessToken
  const role = user?.role

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, role, loading, login, logout, accessToken }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
