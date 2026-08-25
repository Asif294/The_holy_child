import cn from '@/utils/cn'
import { SCHOOL } from '@/utils/constants'
import useSchool from '@/hooks/useSchool'

/**
 * The school crest, drawn inline so it stays crisp at every size and needs no
 * network request. Blue ring, gold open book and a red ribbon — the palette of
 * the school signboard.
 */
export function LogoMark({ className, title }) {
  const { school } = useSchool()
  const label = title || school.name_en || SCHOOL.nameEn

  // An uploaded crest wins; the drawn mark below is the default, not a
  // placeholder, so a school that never uploads one still looks finished.
  if (school.logo_url) {
    return (
      <img
        src={school.logo_url}
        alt={label}
        className={cn('h-9 w-9 shrink-0 rounded-full object-contain', className)}
      />
    )
  }

  return (
    <svg viewBox="0 0 64 64" role="img" aria-label={label} className={cn('h-9 w-9', className)}>
      <defs>
        <linearGradient id="thc-ring" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#2a72d0" />
          <stop offset="100%" stopColor="#0a4189" />
        </linearGradient>
        <linearGradient id="thc-book" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#fcd34d" />
          <stop offset="100%" stopColor="#d9920b" />
        </linearGradient>
      </defs>

      <circle cx="32" cy="32" r="31" fill="url(#thc-ring)" />
      <circle cx="32" cy="32" r="26" fill="#ffffff" />
      <circle cx="32" cy="32" r="26" fill="none" stroke="#f5b324" strokeWidth="1.6" />

      {/* Rising sun of learning */}
      <path d="M14 34a18 18 0 0 1 36 0Z" fill="#eef5fd" />
      <path
        d="M32 13.5l2.4 5 5.5.7-4 3.8 1 5.4-4.9-2.7-4.9 2.7 1-5.4-4-3.8 5.5-.7z"
        fill="#f5b324"
      />

      {/* Open book */}
      <path
        d="M13 36.5c5.8-2.9 12.2-2.9 19 0 6.8-2.9 13.2-2.9 19 0v10.8c-6.4-2.7-12.7-2.7-19 0-6.3-2.7-12.6-2.7-19 0z"
        fill="url(#thc-book)"
      />
      <path d="M32 36.5v10.8" stroke="#8b5a06" strokeWidth="1.3" fill="none" />

      {/* Ribbon */}
      <path d="M11 49h42l-4.5 6.5H15.5z" fill="#c8102e" />
      <path d="M11 49h42l-1.6 2.3H12.6z" fill="#8b1026" opacity="0.5" />
    </svg>
  )
}

/**
 * Splits the wordmark so its tail picks up the gold accent — "SmartSchool"
 * renders as Smart+School. A single-word brand simply stays one colour.
 */
function renderBrand(brand) {
  const match = /^(.*?)(School|Academy|Institute|Campus)$/i.exec(brand)
  if (!match) return brand
  return (
    <>
      {match[1]}
      <span className="text-gold-500">{match[2]}</span>
    </>
  )
}

export function Logo({ className, markClassName, variant = 'dark', showTagline = true }) {
  const { school } = useSchool()
  const isLight = variant === 'light'
  const brand = school.brand_name || SCHOOL.brand
  const locality = (school.address || SCHOOL.address).split(',')[1]?.trim()
  return (
    <span className={cn('flex items-center gap-2.5', className)}>
      <LogoMark className={cn('h-10 w-10 shrink-0', markClassName)} />
      <span className="min-w-0 leading-tight">
        <span className={cn('block text-lg font-extrabold tracking-tight', isLight ? 'text-white' : 'text-brand-800')}>
          {renderBrand(brand)}
        </span>
        {showTagline ? (
          <span className={cn('block truncate text-[11px] font-medium', isLight ? 'text-brand-100' : 'text-slate-500')}>
            {[school.short_name || SCHOOL.shortName, locality].filter(Boolean).join(' · ')}
          </span>
        ) : null}
      </span>
    </span>
  )
}

export default Logo
