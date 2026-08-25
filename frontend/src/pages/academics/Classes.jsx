import { useState } from 'react'
import { Layers, Users } from 'lucide-react'

import Badge from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import useApi from '@/hooks/useApi'
import { classService, sectionService, teacherService } from '@/services'

const TABS = [
  { id: 'classes', label: 'Classes', icon: Layers },
  { id: 'sections', label: 'Sections', icon: Users },
]

const CLASS_COLUMNS = [
  {
    key: 'name',
    header: 'Class',
    render: (row) => (
      <div>
        <p className="font-medium text-slate-900">{row.name}</p>
        {row.name_bn ? (
          <p className="font-bangla text-xs text-slate-500" lang="bn">
            {row.name_bn}
          </p>
        ) : null}
      </div>
    ),
  },
  { key: 'code', header: 'Code', render: (row) => <span className="font-mono text-xs">{row.code}</span> },
  { key: 'order', header: 'Order' },
  { key: 'section_count', header: 'Sections' },
  {
    key: 'student_count',
    header: 'Students',
    render: (row) => <Badge tone="brand">{row.student_count}</Badge>,
  },
]

const CLASS_FIELDS = [
  { name: 'name', label: 'Class name', required: true, placeholder: 'Class 6' },
  { name: 'name_bn', label: 'Bangla name', placeholder: '৬ষ্ঠ শ্রেণি' },
  { name: 'code', label: 'Class code', required: true, placeholder: 'C6' },
  { name: 'order', label: 'Sort order', type: 'number', min: 0, defaultValue: 0, hint: 'Lower numbers appear first.' },
  { name: 'description', label: 'Description', type: 'textarea' },
]

function SectionsTab() {
  const { data: classes } = useApi(() => classService.all(), [], { initialData: [] })
  const { data: teachers } = useApi(() => teacherService.all({ status: 'active' }), [], { initialData: [] })

  const classOptions = (classes ?? []).map((item) => ({ value: item.id, label: item.name }))
  const teacherOptions = (teachers ?? []).map((item) => ({ value: item.id, label: item.full_name }))

  return (
    <CrudPage
      title="Sections"
      description="Sections within each class, and the teacher responsible for them."
      service={sectionService}
      module="class"
      singular="section"
      searchPlaceholder="Search sections…"
      columns={[
        {
          key: 'name',
          header: 'Section',
          render: (row) => (
            <div>
              <p className="font-medium text-slate-900">
                {row.class_name} — {row.name}
              </p>
              {row.room_number ? <p className="text-xs text-slate-500">Room {row.room_number}</p> : null}
            </div>
          ),
        },
        { key: 'class_teacher_name', header: 'Class teacher', render: (row) => row.class_teacher_name ?? '—' },
        { key: 'capacity', header: 'Capacity' },
        {
          key: 'enrolled_count',
          header: 'Enrolled',
          render: (row) => (
            <Badge tone={row.seats_available === 0 ? 'danger' : 'success'}>
              {row.enrolled_count} / {row.capacity}
            </Badge>
          ),
        },
      ]}
      fields={[
        { name: 'school_class', label: 'Class', type: 'select', options: classOptions, required: true },
        { name: 'name', label: 'Section name', required: true, placeholder: 'A' },
        { name: 'capacity', label: 'Capacity', type: 'number', min: 1, defaultValue: 40 },
        { name: 'room_number', label: 'Room number', placeholder: '6A' },
        { name: 'class_teacher', label: 'Class teacher', type: 'select', options: teacherOptions, fullWidth: true },
      ]}
      filters={[{ name: 'school_class', placeholder: 'All classes', options: classOptions }]}
    />
  )
}

export function Classes() {
  const [tab, setTab] = useState('classes')

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

      {tab === 'classes' ? (
        <CrudPage
          title="Classes"
          description="Grade levels offered by the school, from Play Group to Class 10."
          service={classService}
          module="class"
          singular="class"
          columns={CLASS_COLUMNS}
          fields={CLASS_FIELDS}
          searchPlaceholder="Search classes…"
        />
      ) : (
        <SectionsTab />
      )}
    </div>
  )
}

export default Classes
