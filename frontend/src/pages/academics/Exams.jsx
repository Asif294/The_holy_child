import { useMemo } from 'react'

import Badge, { StatusBadge } from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import useApi from '@/hooks/useApi'
import { examService, examTypeService, sessionService } from '@/services'
import { formatDate } from '@/utils/formatters'

const STATUS_OPTIONS = [
  { value: 'planned', label: 'Planned' },
  { value: 'ongoing', label: 'Ongoing' },
  { value: 'completed', label: 'Completed' },
  { value: 'published', label: 'Results published' },
  { value: 'cancelled', label: 'Cancelled' },
]

export function Exams() {
  const { data: types } = useApi(() => examTypeService.all(), [], { initialData: [] })
  const { data: sessions } = useApi(() => sessionService.all(), [], { initialData: [] })

  const typeOptions = useMemo(() => (types ?? []).map((t) => ({ value: t.id, label: t.name })), [types])
  const sessionOptions = useMemo(() => (sessions ?? []).map((s) => ({ value: s.id, label: s.name })), [sessions])

  const columns = [
    {
      key: 'name',
      header: 'Exam',
      render: (row) => (
        <div className="min-w-0">
          <p className="truncate font-medium text-slate-900">{row.name}</p>
          <p className="text-xs text-slate-500">
            {row.exam_type_name ?? 'Uncategorised'} · {row.session_name}
          </p>
        </div>
      ),
    },
    {
      key: 'start_date',
      header: 'Dates',
      render: (row) => (
        <span className="text-sm">
          {formatDate(row.start_date)} — {formatDate(row.end_date)}
        </span>
      ),
    },
    { key: 'schedule_count', header: 'Papers', render: (row) => <Badge tone="neutral">{row.schedule_count}</Badge> },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} label={row.status_display} /> },
  ]

  const fields = [
    { name: 'name', label: 'Exam name', required: true, fullWidth: true, placeholder: 'Half Yearly Examination 2026' },
    { name: 'exam_type', label: 'Exam type', type: 'select', options: typeOptions },
    { name: 'session', label: 'Academic session', type: 'select', options: sessionOptions, required: true },
    { name: 'start_date', label: 'Start date', type: 'date', required: true },
    { name: 'end_date', label: 'End date', type: 'date', required: true },
    { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, defaultValue: 'planned' },
    { name: 'instructions', label: 'Instructions', type: 'textarea', rows: 4 },
  ]

  return (
    <CrudPage
      title="Exams"
      description="Examinations scheduled for each academic session."
      service={examService}
      module="exam"
      singular="exam"
      columns={columns}
      fields={fields}
      searchPlaceholder="Search exams…"
      filters={[
        { name: 'session', placeholder: 'All sessions', options: sessionOptions },
        { name: 'status', placeholder: 'All statuses', options: STATUS_OPTIONS },
      ]}
    />
  )
}

export default Exams
