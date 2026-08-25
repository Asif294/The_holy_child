import { AlertCircle, Search } from 'lucide-react'

import cn from '@/utils/cn'
import Alert from '@/components/ui/Alert'
import EmptyState from '@/components/ui/EmptyState'
import Pagination from '@/components/ui/Pagination'
import { SkeletonRows } from '@/components/ui/Spinner'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'

/**
 * The one table every list screen uses.
 *
 * Columns are described declaratively: `{ key, header, render, className }`.
 * Loading, empty, error and pagination states are handled here so no screen has
 * to reimplement them.
 */
export function DataTable({
  columns,
  rows,
  isLoading,
  error,
  emptyTitle = 'No records found',
  emptyDescription = 'Try adjusting your search or filters.',
  emptyIcon = Search,
  emptyAction,
  getRowKey = (row) => row.id,
  onRowClick,
  toolbar,
  pagination,
  className,
}) {
  return (
    <div className={cn('card overflow-hidden', className)}>
      {toolbar ? <div className="border-b border-slate-200 px-5 py-3.5">{toolbar}</div> : null}

      {error ? (
        <div className="p-5">
          <Alert type="error" title="Could not load this list">
            {error.message}
          </Alert>
        </div>
      ) : isLoading ? (
        <SkeletonRows rows={6} columns={Math.min(columns.length, 5)} />
      ) : rows.length === 0 ? (
        <EmptyState icon={emptyIcon} title={emptyTitle} description={emptyDescription} action={emptyAction} />
      ) : (
        <Table>
          <THead>
            <TR className="hover:bg-transparent">
              {columns.map((column) => (
                <TH key={column.key} className={column.headerClassName}>
                  {column.header}
                </TH>
              ))}
            </TR>
          </THead>
          <TBody>
            {rows.map((row) => (
              <TR
                key={getRowKey(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={onRowClick ? 'cursor-pointer' : undefined}
              >
                {columns.map((column) => (
                  <TD key={column.key} className={column.className}>
                    {column.render ? column.render(row) : (row[column.key] ?? '—')}
                  </TD>
                ))}
              </TR>
            ))}
          </TBody>
        </Table>
      )}

      {pagination && !isLoading && !error && rows.length > 0 ? (
        <div className="border-t border-slate-200">
          <Pagination {...pagination} />
        </div>
      ) : null}
    </div>
  )
}

export function TableErrorHint({ children }) {
  return (
    <p className="flex items-center gap-1.5 text-xs text-crimson-600">
      <AlertCircle className="h-3.5 w-3.5" />
      {children}
    </p>
  )
}

export default DataTable
