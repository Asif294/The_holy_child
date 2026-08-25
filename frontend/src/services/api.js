import axios from 'axios'

import { API_BASE_URL, ERROR_CODES, STORAGE_KEYS } from '@/utils/constants'

/* --------------------------------------------------------------------------
   Token storage — one module owns reading and writing tokens so nothing else
   has to know where they live.
   -------------------------------------------------------------------------- */
export const tokenStore = {
  getAccess: () => localStorage.getItem(STORAGE_KEYS.access),
  getRefresh: () => localStorage.getItem(STORAGE_KEYS.refresh),
  set({ access, refresh }) {
    if (access) localStorage.setItem(STORAGE_KEYS.access, access)
    if (refresh) localStorage.setItem(STORAGE_KEYS.refresh, refresh)
  },
  clear() {
    localStorage.removeItem(STORAGE_KEYS.access)
    localStorage.removeItem(STORAGE_KEYS.refresh)
    localStorage.removeItem(STORAGE_KEYS.user)
  },
}

/* --------------------------------------------------------------------------
   The session-expiry hook. AuthProvider registers a callback here so that a
   failed refresh can tear down React state, rather than this module reaching
   into the router.
   -------------------------------------------------------------------------- */
let onSessionExpired = () => {}
export function setSessionExpiredHandler(handler) {
  onSessionExpired = typeof handler === 'function' ? handler : () => {}
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { Accept: 'application/json' },
  timeout: 30000,
})

/** A bare client for the refresh call — it must not run the interceptors below. */
const refreshClient = axios.create({ baseURL: API_BASE_URL, headers: { Accept: 'application/json' } })

/* --------------------------------------------------------------------------
   Request: attach the access token.
   -------------------------------------------------------------------------- */
api.interceptors.request.use((config) => {
  const token = tokenStore.getAccess()
  if (token && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Let the browser set the multipart boundary itself.
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  return config
})

/* --------------------------------------------------------------------------
   Response: normalise errors, and transparently refresh an expired access
   token exactly once per burst of 401s.
   -------------------------------------------------------------------------- */
let refreshPromise = null

async function refreshAccessToken() {
  const refresh = tokenStore.getRefresh()
  if (!refresh) throw new Error('No refresh token')

  const { data } = await refreshClient.post('/auth/token/refresh/', { refresh })
  tokenStore.set({ access: data.access, refresh: data.refresh })
  return data.access
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error

    if (!response) {
      return Promise.reject(
        normaliseError({
          message: 'Cannot reach the server. Check your connection and try again.',
          code: ERROR_CODES.NETWORK_ERROR,
          status: 0,
        }),
      )
    }

    const isRefreshCall = config?.url?.includes('/auth/token/refresh/')
    const isLoginCall = config?.url?.includes('/auth/login/')

    if (response.status === 401 && !config._retried && !isRefreshCall && !isLoginCall && tokenStore.getRefresh()) {
      config._retried = true
      try {
        // Concurrent 401s share one refresh instead of stampeding the endpoint.
        refreshPromise = refreshPromise || refreshAccessToken().finally(() => {
          refreshPromise = null
        })
        const access = await refreshPromise
        config.headers.Authorization = `Bearer ${access}`
        return api(config)
      } catch {
        tokenStore.clear()
        onSessionExpired()
        return Promise.reject(
          normaliseError({
            message: 'Your session has expired. Please sign in again.',
            code: ERROR_CODES.AUTHENTICATION_FAILED,
            status: 401,
          }),
        )
      }
    }

    if (response.status === 401 && !tokenStore.getRefresh() && !isLoginCall) {
      onSessionExpired()
    }

    return Promise.reject(
      normaliseError({
        message: response.data?.message || defaultMessageFor(response.status),
        code: response.data?.code || ERROR_CODES[response.status] || 'ERROR',
        status: response.status,
        errors: response.data?.errors || {},
      }),
    )
  },
)

function defaultMessageFor(status) {
  switch (status) {
    case 400:
      return 'The request could not be processed.'
    case 401:
      return 'Please sign in to continue.'
    case 403:
      return 'You do not have permission to perform this action.'
    case 404:
      return 'The requested resource was not found.'
    case 422:
      return 'Please correct the highlighted fields.'
    case 429:
      return 'Too many requests. Please slow down and try again.'
    case 500:
    case 502:
    case 503:
      return 'The server ran into a problem. Please try again shortly.'
    default:
      return 'Something went wrong.'
  }
}

/**
 * An `ApiError` carries everything a form or toast needs: a message to show,
 * a machine-readable code to branch on, and per-field errors to render inline.
 */
export class ApiError extends Error {
  constructor({ message, code, status, errors }) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.errors = errors || {}
  }

  /** First error message for a field, if the API reported one. */
  fieldError(field) {
    const value = this.errors[field]
    return Array.isArray(value) ? value[0] : value
  }
}

function normaliseError(payload) {
  return new ApiError(payload)
}

export default api
