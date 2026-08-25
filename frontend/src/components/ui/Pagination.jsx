import { ChevronLeft, ChevronRight } from 'lucide-react'

import cn from '@/utils/cn'

/** Windows the page numbers so a 191-page list still fits on a phone. */
function pageWindow(current, total, span = 1) {
  const pages = new Set([1, total])
  for (let page = current - span; page <= current + span; page += 1) {
    if (page > 1 && page < total) pages.add(page)
  }
  const sorted = [...pages].filter((page) => page >= 1 && page <= total).sort((a, b) => a - b)

  const withGaps = []
  let previous = 0
  for (const page of sorted) {
    if (previous && page - previous > 1) withGaps.push('…')
    withGaps.push(page)
    previous = page
  }
  return withGaps
}

export function Pagination({ page, totalPages, count, pageSize, onChange, className }) {
  if (!totalPages || totalPages <= 1) {
    return count ? (
      <div className={cn('px-5 py-3 text-sm text-slate-500', className)}>
        {count} {count === 1 ? 'record' : 'records'}
      </div>
    ) : null
  }

  const from = (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, count)

  return (
    <nav
      aria-label="Pagination"
      className={cn('flex flex-wrap items-center justify-between gap-3 px-5 py-3', className)}
    >
      <p className="text-sm text-slate-500">
        Showing <span className="font-medium text-slate-700">{from}</span>–
        <span className="font-medium text-slate-700">{to}</span> of{' '}
        <span className="font-medium text-slate-700">{count}</span>
      </p>

      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>

        {pageWindow(page, totalPages).map((entry, index) =>
          entry === '…' ? (
            <span key={`gap-${index}`} className="px-1.5 text-slate-400" aria-hidden="true">
              …
            </span>
          ) : (
            <button
              key={entry}
              type="button"
              onClick={() => onChange(entry)}
              aria-current={entry === page ? 'page' : undefined}
              className={cn(
                'inline-flex h-9 min-w-9 items-center justify-center rounded-lg px-2.5 text-sm font-medium transition-colors',
                entry === page
                  ? 'bg-brand-600 text-white'
                  : 'border border-slate-300 text-slate-600 hover:bg-slate-50',
              )}
            >
              {entry}
            </button>
          ),
        )}

        <button
          type="button"
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </nav>
  )
}

export default Pagination
