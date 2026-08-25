import cn from '@/utils/cn'

const TONES = {
  brand: 'bg-brand-50 text-brand-600',
  violet: 'bg-violet-50 text-violet-600',
  gold: 'bg-gold-50 text-gold-700',
  emerald: 'bg-emerald-50 text-emerald-600',
  crimson: 'bg-crimson-50 text-crimson-600',
  sky: 'bg-sky-50 text-sky-600',
}

export function StatCard({ icon: Icon, label, value, hint, tone = 'brand', isLoading, className }) {
  return (
    <div className={cn('card p-5', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          {isLoading ? (
            <div className="skeleton mt-2.5 h-8 w-24" />
          ) : (
            <p className="mt-2 truncate text-2xl font-bold tracking-tight text-slate-900">{value}</p>
          )}
          {hint && !isLoading ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
        </div>
        <span className={cn('inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl', TONES[tone])}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
    </div>
  )
}

export default StatCard
