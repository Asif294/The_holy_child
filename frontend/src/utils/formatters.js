const DATE_LOCALE = 'en-GB'

export function formatDate(value, options) {
  if (!value) return '—'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(DATE_LOCALE, { day: '2-digit', month: 'short', year: 'numeric', ...options })
}

export function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return `${formatDate(date)} · ${date.toLocaleTimeString(DATE_LOCALE, { hour: '2-digit', minute: '2-digit' })}`
}

/** "3 hours ago" — for activity feeds where the exact timestamp is noise. */
export function formatRelative(value) {
  if (!value) return '—'
  const date = new Date(value)
  const seconds = Math.round((Date.now() - date.getTime()) / 1000)
  if (seconds < 60) return 'just now'

  const units = [
    ['minute', 60],
    ['hour', 60],
    ['day', 24],
    ['week', 7],
    ['month', 4.345],
    ['year', 12],
  ]
  let amount = seconds
  let label = 'second'
  for (const [unit, factor] of units) {
    if (amount < factor) break
    amount = amount / factor
    label = unit
  }
  const rounded = Math.floor(amount)
  return `${rounded} ${label}${rounded === 1 ? '' : 's'} ago`
}

/** Bangladeshi Taka, with the symbol the school's staff actually use. */
export function formatCurrency(value, { withSymbol = true } = {}) {
  const amount = Number(value ?? 0)
  const formatted = amount.toLocaleString('en-BD', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
  return withSymbol ? `৳${formatted}` : formatted
}

export function formatNumber(value) {
  return Number(value ?? 0).toLocaleString('en-US')
}

export function formatPercent(value, digits = 1) {
  return `${Number(value ?? 0).toFixed(digits)}%`
}

export function initialsOf(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

/** Title-cases a snake_case enum value coming back from the API. */
export function humanise(value = '') {
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
