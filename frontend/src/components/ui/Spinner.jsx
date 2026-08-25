import { Loader2 } from 'lucide-react'

import cn from '@/utils/cn'

export function Spinner({ className, label = 'Loading' }) {
  return (
    <span role="status" aria-live="polite">
      <Loader2 className={cn('h-5 w-5 animate-spin text-brand-600', className)} aria-hidden="true" />
      <span className="sr-only">{label}</span>
    </span>
  )
}

export function LoadingState({ label = 'Loading…', className }) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-16 text-slate-500', className)}>
      <Spinner className="h-7 w-7" />
      <p className="text-sm">{label}</p>
    </div>
  )
}

export function SkeletonRows({ rows = 5, columns = 4 }) {
  return (
    <div className="divide-y divide-slate-100">
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex items-center gap-4 px-5 py-4">
          {Array.from({ length: columns }).map((__, columnIndex) => (
            <div
              key={columnIndex}
              className="skeleton h-4"
              style={{ width: columnIndex === 0 ? '28%' : `${Math.max(12, 20 - columnIndex * 2)}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export default Spinner
