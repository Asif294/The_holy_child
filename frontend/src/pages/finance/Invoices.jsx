import { useMemo, useState } from 'react'
import { AlertCircle, CreditCard, Receipt, Search, Wallet } from 'lucide-react'

import { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Select } from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import StatCard from '@/components/dashboard/StatCard'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import { feeCategoryService, invoiceService, paymentService } from '@/services'
import { formatCurrency, formatDate, formatPercent } from '@/utils/formatters'

const STATUS_OPTIONS = [
  { value: 'unpaid', label: 'Unpaid' },
  { value: 'partial', label: 'Partially paid' },
  { value: 'paid', label: 'Paid' },
  { value: 'waived', label: 'Waived' },
  { value: 'cancelled', label: 'Cancelled' },
]

const METHOD_OPTIONS = [
  { value: 'cash', label: 'Cash' },
  { value: 'bkash', label: 'bKash' },
  { value: 'nagad', label: 'Nagad' },
  { value: 'rocket', label: 'Rocket' },
  { value: 'bank', label: 'Bank transfer' },
  { value: 'cheque', label: 'Cheque' },
  { value: 'card', label: 'Card' },
]

export function Invoices() {
  useDocumentTitle('Invoices')

  const toast = useToast()
  const list = usePaginatedList(invoiceService)
  const { data: stats, refetch: refetchStats } = useApi(() => invoiceService.statistics(), [])
  const { data: categories } = useApi(() => feeCategoryService.all(), [], { initialData: [] })

  const [paying, setPaying] = useState(null)
  const [isSaving, setSaving] = useState(false)

  const categoryOptions = useMemo(
    () => (categories ?? []).map((item) => ({ value: item.id, label: item.name })),
    [categories],
  )

  const paymentFields = useMemo(
    () => [
      { name: 'receipt_number', label: 'Receipt number', required: true, placeholder: 'RCP-2026-00001' },
      { name: 'amount', label: 'Amount (৳)', type: 'number', min: 0.01, step: '0.01', required: true },
      { name: 'method', label: 'Method', type: 'select', options: METHOD_OPTIONS, defaultValue: 'cash' },
      { name: 'paid_at', label: 'Paid at', type: 'datetime-local', required: true },
      { name: 'transaction_reference', label: 'Transaction reference' },
      { name: 'note', label: 'Note', type: 'textarea' },
    ],
    [],
  )
  const paymentForm = useResourceForm(paymentFields, null)

  async function handlePayment(event) {
    event.preventDefault()
    setSaving(true)
    try {
      await paymentService.create({ ...paymentForm.payload(), invoice: paying.id })
      toast.success('Payment recorded.')
      setPaying(null)
      list.reload()
      refetchStats()
    } catch (error) {
      paymentForm.setErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    {
      key: 'invoice_number',
      header: 'Invoice',
      render: (row) => (
        <div className="min-w-0">
          <p className="font-mono text-xs text-slate-500">{row.invoice_number}</p>
          <p className="truncate font-medium text-slate-900">{row.title}</p>
        </div>
      ),
    },
    {
      key: 'student_name',
      header: 'Student',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate text-slate-800">{row.student_name}</p>
          <p className="text-xs text-slate-500">{row.class_name ?? '—'}</p>
        </div>
      ),
    },
    { key: 'payable', header: 'Payable', render: (row) => formatCurrency(row.payable) },
    {
      key: 'paid_amount',
      header: 'Paid',
      render: (row) => <span className="text-emerald-700">{formatCurrency(row.paid_amount)}</span>,
    },
    {
      key: 'due_amount',
      header: 'Due',
      render: (row) => (
        <span className={Number(row.due_amount) > 0 ? 'font-semibold text-crimson-600' : 'text-slate-400'}>
          {formatCurrency(row.due_amount)}
        </span>
      ),
    },
    { key: 'due_date', header: 'Due date', render: (row) => formatDate(row.due_date) },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} label={row.status_display} /> },
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-16',
      className: 'text-right',
      render: (row) =>
        ['unpaid', 'partial'].includes(row.status) ? (
          <Can permission="payment.create">
            <button
              type="button"
              onClick={() => setPaying(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-emerald-50 hover:text-emerald-600"
              aria-label={`Record a payment for ${row.invoice_number}`}
              title="Record payment"
            >
              <CreditCard className="h-4 w-4" />
            </button>
          </Can>
        ) : null,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Invoices"
        description="Bills raised against students. Recording a payment re-derives the invoice status automatically."
      />

      <div className="mb-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Receipt} label="Total billed" value={formatCurrency(stats?.total_billed)} tone="brand" />
        <StatCard icon={Wallet} label="Collected" value={formatCurrency(stats?.total_collected)} tone="emerald" />
        <StatCard
          icon={AlertCircle}
          label="Outstanding"
          value={formatCurrency(stats?.total_outstanding)}
          hint={`${stats?.overdue_count ?? 0} overdue`}
          tone="crimson"
        />
        <StatCard
          icon={CreditCard}
          label="Collection rate"
          value={formatPercent(stats?.collection_rate)}
          hint={`${stats?.invoice_count ?? 0} invoices`}
          tone="gold"
        />
      </div>

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={Receipt}
        emptyTitle="No invoices found"
        emptyDescription="Adjust the filters, or raise an invoice against a student."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search invoice or student…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search invoices"
            />
            <Select
              className="w-auto min-w-[9rem]"
              placeholder="All statuses"
              options={STATUS_OPTIONS}
              value={list.filters.status ?? ''}
              onChange={(event) => list.setFilter('status', event.target.value)}
              aria-label="Filter by status"
            />
            <Select
              className="w-auto min-w-[10rem]"
              placeholder="All fee heads"
              options={categoryOptions}
              value={list.filters.category ?? ''}
              onChange={(event) => list.setFilter('category', event.target.value)}
              aria-label="Filter by fee head"
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

      <Modal
        isOpen={Boolean(paying)}
        onClose={() => setPaying(null)}
        title="Record a payment"
        description={
          paying
            ? `${paying.student_name} · ${paying.invoice_number} · ${formatCurrency(paying.due_amount)} outstanding`
            : undefined
        }
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setPaying(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="payment-form" isLoading={isSaving}>
              Record payment
            </Button>
          </div>
        }
      >
        <form id="payment-form" onSubmit={handlePayment} noValidate>
          <ResourceForm
            fields={paymentFields}
            values={paymentForm.values}
            errors={paymentForm.errors}
            onChange={paymentForm.change}
          />
        </form>
      </Modal>
    </div>
  )
}

export default Invoices
