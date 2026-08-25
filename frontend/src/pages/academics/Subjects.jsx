import Badge from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import { subjectService } from '@/services'

const CATEGORY_OPTIONS = [
  { value: 'compulsory', label: 'Compulsory' },
  { value: 'optional', label: 'Optional' },
  { value: 'extra', label: 'Extra-curricular' },
]

const COLUMNS = [
  {
    key: 'name',
    header: 'Subject',
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
  {
    key: 'category',
    header: 'Category',
    render: (row) => <Badge tone={row.category === 'compulsory' ? 'brand' : 'neutral'}>{row.category_display}</Badge>,
  },
  { key: 'full_marks', header: 'Full marks' },
  { key: 'pass_marks', header: 'Pass marks' },
  { key: 'class_count', header: 'Classes' },
]

const FIELDS = [
  { name: 'name', label: 'Subject name', required: true, placeholder: 'Mathematics' },
  { name: 'name_bn', label: 'Bangla name', placeholder: 'গণিত' },
  { name: 'code', label: 'Subject code', required: true, placeholder: 'MAT' },
  { name: 'category', label: 'Category', type: 'select', options: CATEGORY_OPTIONS, defaultValue: 'compulsory' },
  { name: 'full_marks', label: 'Full marks', type: 'number', min: 1, defaultValue: 100 },
  { name: 'pass_marks', label: 'Pass marks', type: 'number', min: 0, defaultValue: 33 },
  { name: 'description', label: 'Description', type: 'textarea' },
]

export function Subjects() {
  return (
    <CrudPage
      title="Subjects"
      description="The subject catalogue taught across the school."
      service={subjectService}
      module="subject"
      singular="subject"
      columns={COLUMNS}
      fields={FIELDS}
      filters={[{ name: 'category', placeholder: 'All categories', options: CATEGORY_OPTIONS }]}
      searchPlaceholder="Search by name or code…"
    />
  )
}

export default Subjects
