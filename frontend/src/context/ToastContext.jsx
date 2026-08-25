import { createContext, useCallback, useMemo, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from 'lucide-react'

export const ToastContext = createContext(null)

const ICONS = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const TONES = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900',
  error: 'border-crimson-200 bg-crimson-50 text-crimson-900',
  warning: 'border-gold-200 bg-gold-50 text-gold-900',
  info: 'border-brand-200 bg-brand-50 text-brand-900',
}

const ICON_TONES = {
  success: 'text-emerald-600',
  error: 'text-crimson-600',
  warning: 'text-gold-600',
  info: 'text-brand-600',
}

/** Lightweight, dependency-free notifications. */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const nextId = useRef(1)

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const push = useCallback(
    (message, { type = 'info', duration = 4500 } = {}) => {
      const id = nextId.current++
      // Newest first: the stack hangs from the top, so a new toast belongs at
      // the top edge where the eye already is. Appending instead would push
      // each new one further down, and dismissing the oldest would jump the
      // rest upwards.
      setToasts((current) => [{ id, message, type }, ...current])
      if (duration) setTimeout(() => dismiss(id), duration)
      return id
    },
    [dismiss],
  )

  const value = useMemo(
    () => ({
      toast: push,
      success: (message, options) => push(message, { ...options, type: 'success' }),
      error: (message, options) => push(message, { ...options, type: 'error' }),
      warning: (message, options) => push(message, { ...options, type: 'warning' }),
      info: (message, options) => push(message, { ...options, type: 'info' }),
      dismiss,
    }),
    [push, dismiss],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Centred at the top. `top-20` clears the sticky 4rem topbar, so a toast
          never sits over the search box, the bell or the profile menu, and the
          padding keeps it off the screen edges on a narrow phone. */}
      <div
        className="pointer-events-none fixed left-1/2 top-20 z-[100] flex w-full max-w-sm -translate-x-1/2 flex-col gap-2 px-4 sm:px-0"
        role="region"
        aria-label="Notifications"
      >
        {toasts.map((toast) => {
          const Icon = ICONS[toast.type] ?? Info
          return (
            <div
              key={toast.id}
              role="status"
              className={`pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 shadow-[var(--shadow-float)] ${TONES[toast.type]}`}
            >
              <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${ICON_TONES[toast.type]}`} aria-hidden="true" />
              <p className="flex-1 text-sm font-medium leading-snug">{toast.message}</p>
              <button
                type="button"
                onClick={() => dismiss(toast.id)}
                className="shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}
