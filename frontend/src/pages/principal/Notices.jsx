import { Send } from 'lucide-react'

import Badge, { StatusBadge } from '@/components/ui/Badge'
import Can from '@/components/common/Can'
import CrudPage from '@/components/common/CrudPage'
import useToast from '@/hooks/useToast'
import { noticeService } from '@/services'
import { formatDate } from '@/utils/formatters'

const AUDIENCE_OPTIONS = [
  { value: 'all', label: 'Everyone' },
  { value: 'staff', label: 'Staff only' },
  { value: 'teachers', label: 'Teachers' },
  { value: 'students', label: 'Students' },
  { value: 'parents', label: 'Parents' },
]

const PRIORITY_OPTIONS = [
  { value: 'normal', label: 'Normal' },
  { value: 'important', label: 'Important' },
  { value: 'urgent', label: 'Urgent' },
]

const FIELDS = [
  { name: 'title', label: 'Title', required: true, fullWidth: true, placeholder: 'Half Yearly Examination Routine' },
  { name: 'body', label: 'Notice text', type: 'textarea', rows: 6, required: true },
  { name: 'audience', label: 'Audience', type: 'select', options: AUDIENCE_OPTIONS, defaultValue: 'all' },
  { name: 'priority', label: 'Priority', type: 'select', options: PRIORITY_OPTIONS, defaultValue: 'normal' },
  { name: 'published_at', label: 'Publish at', type: 'datetime-local' },
  { name: 'expires_at', label: 'Expires at', type: 'datetime-local' },
  { name: 'is_published', label: 'Publish immediately', type: 'checkbox' },
]

export function Notices() {
  const toast = useToast()

  const columns = [
    {
      key: 'title',
      header: 'Notice',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.title}</p>
          <p className="line-clamp-1 text-xs text-slate-500">{row.body}</p>
        </div>
      ),
    },
    { key: 'audience_display', header: 'Audience', render: (row) => <Badge tone="neutral">{row.audience_display}</Badge> },
    {
      key: 'priority',
      header: 'Priority',
      render: (row) => <StatusBadge status={row.priority} label={row.priority_display} />,
    },
    {
      key: 'is_published',
      header: 'Status',
      render: (row) =>
        row.is_published ? <Badge tone="success">Published</Badge> : <Badge tone="warning">Draft</Badge>,
    },
    { key: 'published_at', header: 'Published', render: (row) => formatDate(row.published_at) },
    { key: 'issued_by_name', header: 'Issued by', render: (row) => row.issued_by_name ?? '—' },
  ]

  return (
    <CrudPage
      title="Notices"
      description="Notices issued by the principal's office. Drafts stay hidden until published."
      service={noticeService}
      module="notice"
      singular="notice"
      columns={columns}
      fields={FIELDS}
      searchPlaceholder="Search notices…"
      filters={[
        { name: 'audience', placeholder: 'All audiences', options: AUDIENCE_OPTIONS },
        { name: 'priority', placeholder: 'All priorities', options: PRIORITY_OPTIONS },
      ]}
      toPayload={(payload, values) => ({ ...payload, is_published: Boolean(values.is_published) })}
      rowActions={(row, reload) =>
        row.is_published ? null : (
          <Can permission="notice.update">
            <button
              type="button"
              onClick={async () => {
                try {
                  await noticeService.publish(row.id)
                  toast.success('Notice published.')
                  reload()
                } catch (error) {
                  toast.error(error.message)
                }
              }}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-emerald-50 hover:text-emerald-600"
              aria-label={`Publish ${row.title}`}
              title="Publish"
            >
              <Send className="h-4 w-4" />
            </button>
          </Can>
        )
      }
    />
  )
}

export default Notices
