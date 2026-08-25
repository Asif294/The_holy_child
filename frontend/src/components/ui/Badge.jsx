import cn from '@/utils/cn'

const TONES = {
  neutral: 'bg-slate-100 text-slate-700 ring-slate-200',
  brand: 'bg-brand-50 text-brand-700 ring-brand-200',
  success: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  warning: 'bg-gold-50 text-gold-800 ring-gold-200',
  danger: 'bg-crimson-50 text-crimson-700 ring-crimson-200',
  info: 'bg-sky-50 text-sky-700 ring-sky-200',
  purple: 'bg-violet-50 text-violet-700 ring-violet-200',
}

/** Maps the API's status enums to a tone, so status colours stay consistent. */
export const STATUS_TONES = {
  active: 'success',
  present: 'success',
  paid: 'success',
  approved: 'success',
  published: 'success',
  completed: 'success',
  late: 'warning',
  partial: 'warning',
  pending: 'warning',
  on_leave: 'warning',
  leave: 'warning',
  planned: 'info',
  ongoing: 'info',
  unpaid: 'danger',
  absent: 'danger',
  rejected: 'danger',
  suspended: 'danger',
  dropped: 'danger',
  cancelled: 'neutral',
  waived: 'neutral',
  resigned: 'neutral',
  retired: 'neutral',
  transferred: 'neutral',
  graduated: 'brand',
  holiday: 'purple',
}

export function Badge({ tone = 'neutral', size = 'sm', className, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full font-medium ring-1 ring-inset whitespace-nowrap',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm',
        TONES[tone] ?? TONES.neutral,
        className,
      )}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status, label, className }) {
  const tone = STATUS_TONES[status] ?? 'neutral'
  const text = label ?? String(status ?? '').replace(/_/g, ' ')
  return (
    <Badge tone={tone} className={cn('capitalize', className)}>
      {text || '—'}
    </Badge>
  )
}

export default Badge
