import { CreditCard, Search } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import Input, { Select } from '@/components/ui/Input'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import { paymentService } from '@/services'
import { formatCurrency, formatDateTime } from '@/utils/formatters'

const METHOD_OPTIONS = [
  { value: 'cash', label: 'Cash' },
  { value: 'bkash', label: 'bKash' },
  { value: 'nagad', label: 'Nagad' },
  { value: 'rocket', label: 'Rocket' },
  { value: 'bank', label: 'Bank transfer' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'card', label: 'Card' },
]

export function Payments() {
  useDocumentTitle('Payments')

  const list = usePaginatedList(paymentService)

  const columns = [
    {
      key: 'receipt_number',
      header: 'Receipt',
      render: (row) => <span className="font-mono text-xs text-slate-600">{row.receipt_number}</span>,
    },
    {
      key: 'student_name',
      header: 'Student',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.student_name}</p>
          <p className="font-mono text-xs text-slate-500">{row.invoice_number}</p>
        </div>
      ),
    },
    {
      key: 'amount',
      header: 'Amount',
      render: (row) => <span className="font-semibold text-slate-900">{formatCurrency(row.amount)}</span>,
    },
    { key: 'method_display', header: 'Method', render: (row) => <Badge tone="neutral">{row.method_display}</Badge> },
    {
      key: 'transaction_reference',
      header: 'Reference',
      render: (row) => row.transaction_reference || '—',
    },
    { key: 'paid_at', header: 'Paid at', render: (row) => formatDateTime(row.paid_at) },
    { key: 'received_by_name', header: 'Received by', render: (row) => row.received_by_name ?? '—' },
  ]

  return (
    <div>
      <PageHeader title="Payments" description="Every payment received against an invoice, newest first." />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={CreditCard}
        emptyTitle="No payments recorded"
        emptyDescription="Payments appear here as soon as they are recorded against an invoice."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search receipt, student or reference…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search payments"
            />
            <Select
              className="w-auto min-w-[10rem]"
              placeholder="All methods"
              options={METHOD_OPTIONS}
              value={list.filters.method ?? ''}
              onChange={(event) => list.setFilter('method', event.target.value)}
              aria-label="Filter by method"
            />
          </div>
        }
        pagination={{
          page: list.page,
          totalPages: list.totalPages,
          count: list.count,
          pageSize: list.pageSize,
          onChange: list.setPage,
        }}
      />
    </div>
  )
}

export default Payments
