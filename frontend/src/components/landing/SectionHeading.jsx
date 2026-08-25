import cn from '@/utils/cn'

/**
 * The shared heading for every public section.
 *
 * Five sections repeating the same eyebrow/title/lede stack is exactly the kind
 * of thing that drifts three pixels apart if each writes its own.
 */
export function SectionHeading({ eyebrow, title, description, align = 'center', className, tone = 'light' }) {
  const isDark = tone === 'dark'
  return (
    <div
      className={cn(
        'max-w-2xl',
        align === 'center' && 'mx-auto text-center',
        className,
      )}
    >
      {eyebrow ? (
        <span
          className={cn(
            'inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide',
            isDark ? 'bg-white/10 text-gold-300' : 'bg-brand-50 text-brand-700',
          )}
        >
          {eyebrow}
        </span>
      ) : null}
      <h2
        className={cn(
          'mt-4 text-3xl font-bold tracking-tight sm:text-4xl',
          isDark ? 'text-white' : 'text-slate-900',
        )}
      >
        {title}
      </h2>
      {description ? (
        <p className={cn('mt-4 text-base leading-relaxed', isDark ? 'text-brand-100' : 'text-slate-600')}>
          {description}
        </p>
      ) : null}
    </div>
  )
}

export default SectionHeading
