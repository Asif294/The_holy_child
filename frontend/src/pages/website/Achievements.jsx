import Badge from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import { achievementService } from '@/services'

const COLUMNS = [
  {
    key: 'title',
    header: 'Achievement',
    render: (row) => (
      <div className="min-w-0">
        <p className="truncate font-medium text-slate-900">{row.title}</p>
        {row.description ? <p className="truncate text-xs text-slate-500">{row.description}</p> : null}
      </div>
    ),
  },
  {
    key: 'metric',
    header: 'Figure',
    render: (row) => (row.metric ? <span className="font-semibold text-brand-700">{row.metric}</span> : '—'),
  },
  { key: 'year', header: 'Year', render: (row) => row.year || '—' },
  { key: 'order', header: 'Order', headerClassName: 'w-20' },
  {
    key: 'is_active',
    header: 'Status',
    render: (row) => (
      <Badge tone={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Showing' : 'Hidden'}</Badge>
    ),
  },
]

const FIELDS = [
  { name: 'title', label: 'Achievement', required: true, placeholder: '100% pass rate in the SSC examination' },
  { name: 'year', label: 'Year', placeholder: '2025' },
  {
    name: 'metric',
    label: 'Figure to show large',
    placeholder: '100%',
    hint: 'Optional — a short number or place, e.g. "100%", "1st", "12".',
  },
  { name: 'order', label: 'Order', type: 'number', min: 0, defaultValue: 0 },
  { name: 'description', label: 'Description', type: 'textarea', rows: 3 },
  { name: 'is_active', label: 'Show on the website', type: 'checkbox', defaultValue: true },
]

/** The milestones shown beside the About section on the public site. */
export function Achievements() {
  return (
    <CrudPage
      title="Achievements"
      description="Milestones shown in the About section of the school's public home page."
      service={achievementService}
      module="content"
      singular="achievement"
      columns={COLUMNS}
      fields={FIELDS}
      searchPlaceholder="Search achievements…"
      emptyTitle="No achievements recorded"
      emptyDescription="Add the results, awards and records the school is proud of."
    />
  )
}

export default Achievements
