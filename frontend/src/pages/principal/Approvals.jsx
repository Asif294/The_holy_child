import { useState } from 'react'
import { Check, Plus, Search, Stamp, X } from 'lucide-react'

import Badge, { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Select, Textarea } from '@/components/ui/Input'
import Modal from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import { approvalService } from '@/services'
import { formatDate } from '@/utils/formatters'

const CATEGORY_OPTIONS = [
  { value: 'leave', label: 'Leave request' },
  { value: 'expense', label: 'Expense approval' },
  { value: 'result', label: 'Result publication' },
  { value: 'admission', label: 'Admission approval' },
  { value: 'event', label: 'Event approval' },
  { value: 'other', label: 'Other' },
]

const STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'cancelled', label: 'Cancelled' },
]

const FIELDS = [
  { name: 'title', label: 'Title', required: true, fullWidth: true, placeholder: 'Casual leave for three days' },
  { name: 'category', label: 'Category', type: 'select', options: CATEGORY_OPTIONS, defaultValue: 'other' },
  { name: 'details', label: 'Details', type: 'textarea', rows: 5 },
]

export function Approvals() {
  useDocumentTitle('Approvals')

  const toast = useToast()
  const list = usePaginatedList(approvalService)

  const [creating, setCreating] = useState(false)
  const [deciding, setDeciding] = useState(null)
  const [decision, setDecision] = useState('approved')
  const [note, setNote] = useState('')
  const [isSaving, setSaving] = useState(false)

  const form = useResourceForm(FIELDS, null)

  async function handleCreate(event) {
    event.preventDefault()
    setSaving(true)
    try {
      await approvalService.create(form.payload())
      toast.success('Request submitted for the principal’s decision.')
      setCreating(false)
      list.reload()
    } catch (error) {
      form.setErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDecide(event) {
    event.preventDefault()
    setSaving(true)
    try {
      await approvalService.decide(deciding.id, decision, note)
      toast.success(`Request ${decision}.`)
      setDeciding(null)
      setNote('')
      list.reload()
    } catch (error) {
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  function openDecision(row, initial) {
    setDeciding(row)
    setDecision(initial)
    setNote('')
  }

  const columns = [
    {
      key: 'title',
      header: 'Request',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.title}</p>
          <p className="line-clamp-1 text-xs text-slate-500">{row.details}</p>
        </div>
      ),
    },
    { key: 'category_display', header: 'Category', render: (row) => <Badge tone="neutral">{row.category_display}</Badge> },
    { key: 'requested_by_name', header: 'Requested by', render: (row) => row.requested_by_name ?? '—' },
    { key: 'created_at', header: 'Raised', render: (row) => formatDate(row.created_at) },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} label={row.status_display} /> },
    {
      key: 'decided_by_name',
      header: 'Decided by',
      render: (row) => (row.decided_by_name ? `${row.decided_by_name} · ${formatDate(row.decided_at)}` : '—'),
    },
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-28',
      className: 'text-right',
      render: (row) =>
        row.status === 'pending' ? (
          <Can permission="principal.approve">
            <div className="flex items-center justify-end gap-1">
              <button
                type="button"
                onClick={() => openDecision(row, 'approved')}
                className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-emerald-50 hover:text-emerald-600"
                aria-label={`Approve ${row.title}`}
                title="Approve"
              >
                <Check className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => openDecision(row, 'rejected')}
                className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-crimson-50 hover:text-crimson-600"
                aria-label={`Reject ${row.title}`}
                title="Reject"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </Can>
        ) : null,
    },
  ]

  return (
    <div>
      <PageHeader
        title="Approvals"
        description="Requests routed to the principal. Anyone may raise one; only a holder of principal.approve can decide."
        actions={
          <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setCreating(true)}>
            Raise a request
          </Button>
        }
      />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={Stamp}
        emptyTitle="No approval requests"
        emptyDescription="Raise a request to route it to the principal for a decision."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search requests…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search approval requests"
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
              placeholder="All categories"
              options={CATEGORY_OPTIONS}
              value={list.filters.category ?? ''}
              onChange={(event) => list.setFilter('category', event.target.value)}
              aria-label="Filter by category"
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
        isOpen={creating}
        onClose={() => setCreating(false)}
        title="Raise an approval request"
        description="The request is recorded against your account and sent to the principal's office."
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setCreating(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="approval-form" isLoading={isSaving}>
              Submit request
            </Button>
          </div>
        }
      >
        <form id="approval-form" onSubmit={handleCreate} noValidate>
          <ResourceForm fields={FIELDS} values={form.values} errors={form.errors} onChange={form.change} />
        </form>
      </Modal>

      <Modal
        isOpen={Boolean(deciding)}
        onClose={() => setDeciding(null)}
        title={decision === 'approved' ? 'Approve this request' : 'Reject this request'}
        description={deciding?.title}
        size="md"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setDeciding(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="decision-form"
              variant={decision === 'approved' ? 'primary' : 'danger'}
              isLoading={isSaving}
            >
              {decision === 'approved' ? 'Approve' : 'Reject'}
            </Button>
          </div>
        }
      >
        <form id="decision-form" onSubmit={handleDecide}>
          <Textarea
            label="Decision note"
            rows={4}
            placeholder="Optional note explaining the decision."
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </form>
      </Modal>
    </div>
  )
}

export default Approvals
