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
 * Splits a wordmark so its tail picks up the gold accent — "SmartSchool"
 * renders as Smart+School, "…Pre-Cadet & High School" keeps its last word in
 * gold. A name that does not end in one of these words simply stays one colour.
 */
function renderWordmark(name) {
  const match = /^(.*?)(School|Academy|Institute|Campus|College|Madrasah)$/i.exec(name)
  if (!match) return name
  return (
    <>
      {match[1]}
      <span className="text-gold-500">{match[2]}</span>
    </>
  )
}

/**
 * The crest plus a wordmark.
 *
 * `primary` decides which name leads. Everywhere a person sees the school —
 * the public site, the sign-in page, the dashboard sidebar — that is the
 * school's own full name. `brand_name` is the product wordmark and stays out
 * of the way, in tab titles and the site footer.
 *
 * `multiline` is for narrow columns: a full school name does not fit one line
 * of a 16rem sidebar, and truncating a school's name to "The Holy Child
 * Pre-…" is worse than wrapping it onto two.
 *
 * Both names come from Settings, so a rename reaches every surface at once.
 */
export function Logo({
  className,
  markClassName,
  variant = 'dark',
  showTagline = true,
  primary = 'brand',
  multiline = false,
}) {
  const { school } = useSchool()
  const isLight = variant === 'light'
  const isSchoolFirst = primary === 'school'

  const locality = (school.address || SCHOOL.address).split(',')[1]?.trim()
  const shortName = school.short_name || SCHOOL.shortName

  const headline = isSchoolFirst ? school.name_en || SCHOOL.nameEn : school.brand_name || SCHOOL.brand
  // Under the school's full name the Bangla name is the more useful second
  // line; under the product wordmark it is "which school, where".
  const tagline = isSchoolFirst
    ? school.name_bn || [shortName, locality].filter(Boolean).join(' · ')
    : [shortName, locality].filter(Boolean).join(' · ')

  return (
    <span className={cn('flex items-center gap-2.5', className)}>
      <LogoMark className={cn('h-10 w-10 shrink-0', markClassName)} />
      <span
        className={cn(
          'min-w-0 leading-tight',
          // A full school name is several times longer than a wordmark, so on
          // a wide header it gets room to grow — and a ceiling so it can never
          // crowd the nav.
          isSchoolFirst && !multiline && 'max-w-[13rem] sm:max-w-sm lg:max-w-lg',
        )}
      >
        <span
          className={cn(
            'block font-extrabold tracking-tight',
            multiline ? 'line-clamp-2 text-[13px] leading-[1.2]' : 'truncate',
            !multiline && (isSchoolFirst ? 'text-base lg:text-lg' : 'text-lg'),
            isLight ? 'text-white' : 'text-brand-800',
          )}
          title={isSchoolFirst ? headline : undefined}
        >
          {renderWordmark(headline)}
        </span>
        {showTagline && tagline ? (
          <span
            className={cn(
              'block truncate text-[11px] font-medium',
              isSchoolFirst && school.name_bn && 'font-bangla text-xs',
              isLight ? 'text-brand-100' : 'text-slate-500',
            )}
            lang={isSchoolFirst && school.name_bn ? 'bn' : undefined}
          >
            {tagline}
          </span>
        ) : null}
      </span>
    </span>
  )
}

export default Logo
