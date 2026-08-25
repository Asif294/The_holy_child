import { useMemo, useState } from 'react'
import { Receipt, Tags } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import useApi from '@/hooks/useApi'
import { classService, feeCategoryService, feeStructureService, sessionService } from '@/services'
import { formatCurrency } from '@/utils/formatters'

const FREQUENCY_OPTIONS = [
  { value: 'one_time', label: 'One time' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'yearly', label: 'Yearly' },
]

const TABS = [
  { id: 'categories', label: 'Fee heads', icon: Tags },
  { id: 'structures', label: 'Fee structures', icon: Receipt },
]

function CategoriesTab() {
  return (
    <CrudPage
      title="Fee heads"
      description="The billable heads the school charges against — tuition, admission, exam and more."
      service={feeCategoryService}
      module="fee"
      singular="fee head"
      searchPlaceholder="Search fee heads…"
      columns={[
        { key: 'name', header: 'Name', render: (row) => <span className="font-medium text-slate-900">{row.name}</span> },
        { key: 'code', header: 'Code', render: (row) => <span className="font-mono text-xs">{row.code}</span> },
        { key: 'frequency_display', header: 'Frequency', render: (row) => <Badge tone="neutral">{row.frequency_display}</Badge> },
        { key: 'description', header: 'Description', render: (row) => row.description || '—' },
      ]}
      fields={[
        { name: 'name', label: 'Name', required: true, placeholder: 'Tuition Fee' },
        { name: 'code', label: 'Code', required: true, placeholder: 'TUI' },
        { name: 'frequency', label: 'Frequency', type: 'select', options: FREQUENCY_OPTIONS, defaultValue: 'monthly' },
        { name: 'description', label: 'Description', type: 'textarea' },
      ]}
      filters={[{ name: 'frequency', placeholder: 'All frequencies', options: FREQUENCY_OPTIONS }]}
    />
  )
}

function StructuresTab() {
  const { data: classes } = useApi(() => classService.all(), [], { initialData: [] })
  const { data: categories } = useApi(() => feeCategoryService.all(), [], { initialData: [] })
  const { data: sessions } = useApi(() => sessionService.all(), [], { initialData: [] })

  const classOptions = useMemo(() => (classes ?? []).map((c) => ({ value: c.id, label: c.name })), [classes])
  const categoryOptions = useMemo(
    () => (categories ?? []).map((c) => ({ value: c.id, label: c.name })),
    [categories],
  )
  const sessionOptions = useMemo(() => (sessions ?? []).map((s) => ({ value: s.id, label: s.name })), [sessions])

  return (
    <CrudPage
      title="Fee structures"
      description="What each class pays under each fee head, per academic session."
      service={feeStructureService}
      module="fee"
      singular="fee structure"
      searchPlaceholder="Search structures…"
      columns={[
        { key: 'class_name', header: 'Class', render: (row) => <span className="font-medium text-slate-900">{row.class_name}</span> },
        { key: 'category_name', header: 'Fee head' },
        { key: 'session_name', header: 'Session' },
        {
          key: 'amount',
          header: 'Amount',
          render: (row) => <span className="font-semibold text-slate-900">{formatCurrency(row.amount)}</span>,
        },
        { key: 'due_day', header: 'Due day', render: (row) => `Day ${row.due_day}` },
      ]}
      fields={[
        { name: 'session', label: 'Academic session', type: 'select', options: sessionOptions, required: true },
        { name: 'school_class', label: 'Class', type: 'select', options: classOptions, required: true },
        { name: 'category', label: 'Fee head', type: 'select', options: categoryOptions, required: true },
        { name: 'amount', label: 'Amount (৳)', type: 'number', min: 0, step: '0.01', required: true },
        { name: 'due_day', label: 'Due day of month', type: 'number', min: 1, max: 31, defaultValue: 10 },
      ]}
      filters={[
        { name: 'school_class', placeholder: 'All classes', options: classOptions },
        { name: 'category', placeholder: 'All fee heads', options: categoryOptions },
      ]}
    />
  )
}

export function Fees() {
  const [tab, setTab] = useState('categories')

  return (
    <div>
      <div className="mb-6 flex gap-1 border-b border-slate-200">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            onClick={() => setTab(entry.id)}
            className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === entry.id
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            }`}
          >
            <entry.icon className="h-4 w-4" aria-hidden="true" />
            {entry.label}
          </button>
        ))}
      </div>

      {tab === 'categories' ? <CategoriesTab /> : <StructuresTab />}
    </div>
  )
}

export default Fees
