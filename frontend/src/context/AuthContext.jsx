import { createContext, useCallback, useEffect, useMemo, useRef, useState } from 'react'

import authService from '@/services/authService'
import { setSessionExpiredHandler, tokenStore } from '@/services/api'
import { STORAGE_KEYS } from '@/utils/constants'

export const AuthContext = createContext(null)

function readCachedUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEYS.user)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function cacheUser(user) {
  if (user) localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user))
  else localStorage.removeItem(STORAGE_KEYS.user)
}

/**
 * Holds the signed-in identity and the permission codes that come with it.
 *
 * The cached user is shown immediately on boot so the shell does not flash,
 * then `/auth/me/` re-validates it against the server. The server's answer
 * always wins — the cache is a rendering optimisation, never an authority.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(readCachedUser)
  const [isLoading, setIsLoading] = useState(Boolean(tokenStore.getAccess()))
  const [sessionExpired, setSessionExpired] = useState(false)
  const bootstrapped = useRef(false)

  const applyUser = useCallback((nextUser) => {
    setUser(nextUser)
    cacheUser(nextUser)
  }, [])

  const logout = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        await authService.logout().catch(() => {})
      } else {
        tokenStore.clear()
      }
      applyUser(null)
    },
    [applyUser],
  )

  // A refresh failure anywhere in the app lands here.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      tokenStore.clear()
      applyUser(null)
      setSessionExpired(true)
    })
    return () => setSessionExpiredHandler(null)
  }, [applyUser])

  // Rehydrate from the stored token on first mount.
  useEffect(() => {
    if (bootstrapped.current) return
    bootstrapped.current = true

    if (!tokenStore.getAccess()) {
      setIsLoading(false)
      return
    }

    authService
      .me()
      .then(applyUser)
      .catch(() => {
        tokenStore.clear()
        applyUser(null)
      })
      .finally(() => setIsLoading(false))
  }, [applyUser])

  const login = useCallback(
    async (credentials) => {
      const data = await authService.login(credentials)
      setSessionExpired(false)
      // The login payload is compact; fetch the full profile for the shell.
      const profile = await authService.me().catch(() => data.user)
      applyUser(profile)
      return profile
    },
    [applyUser],
  )

  const register = useCallback(
    async (payload) => {
      const data = await authService.register(payload)
      setSessionExpired(false)
      const profile = await authService.me().catch(() => data.user)
      applyUser(profile)
      return profile
    },
    [applyUser],
  )

  const refreshUser = useCallback(async () => {
    const profile = await authService.me()
    applyUser(profile)
    return profile
  }, [applyUser])

  const permissions = useMemo(() => new Set(user?.permissions ?? []), [user])

  const hasPermission = useCallback(
    (code) => {
      if (!user) return false
      if (user.is_superuser) return true
      if (!code) return true
      return permissions.has(code)
    },
    [permissions, user],
  )

  const hasAnyPermission = useCallback(
    (codes = []) => {
      if (!user) return false
      if (user.is_superuser) return true
      if (!codes.length) return true
      return codes.some((code) => permissions.has(code))
    },
    [permissions, user],
  )

  const hasAllPermissions = useCallback(
    (codes = []) => {
      if (!user) return false
      if (user.is_superuser) return true
      return codes.every((code) => permissions.has(code))
    },
    [permissions, user],
  )

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      sessionExpired,
      permissions: user?.permissions ?? [],
      role: user?.role?.name ?? user?.role ?? null,
      login,
      register,
      logout,
      refreshUser,
      updateUser: applyUser,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
      dismissSessionExpiry: () => setSessionExpired(false),
    }),
    [
      user,
      isLoading,
      sessionExpired,
      login,
      register,
      logout,
      refreshUser,
      applyUser,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions,
    ],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
