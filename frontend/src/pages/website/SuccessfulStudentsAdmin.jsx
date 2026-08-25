import { useMemo } from 'react'
import { Star } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import { successfulStudentService } from '@/services'

/** The last handful of years, newest first — enough for the filter dropdown. */
function recentYears(span = 8) {
  const thisYear = new Date().getFullYear()
  return Array.from({ length: span }, (unused, offset) => {
    const year = String(thisYear - offset)
    return { value: year, label: year }
  })
}

const COLUMNS = [
  {
    key: 'full_name',
    header: 'Student',
    render: (row) => (
      <div className="flex min-w-0 items-center gap-3">
        <Avatar src={row.photo_url} name={row.full_name} size="sm" className="shrink-0" />
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 truncate font-medium text-slate-900">
            {row.full_name}
            {row.is_featured ? (
              <Star className="h-3.5 w-3.5 shrink-0 fill-gold-400 text-gold-500" aria-label="Featured" />
            ) : null}
          </p>
          <p className="truncate text-xs text-slate-500">
            {[row.student_class, row.section && `Section ${row.section}`, row.roll_number && `Roll ${row.roll_number}`]
              .filter(Boolean)
              .join(' · ') || '—'}
          </p>
        </div>
      </div>
    ),
  },
  { key: 'academic_year', header: 'Year' },
  { key: 'exam_name', header: 'Exam', render: (row) => row.exam_name || '—' },
  {
    key: 'result',
    header: 'Result',
    render: (row) => (
      <span className="font-semibold text-brand-700">{row.result || (row.gpa ? `GPA ${row.gpa}` : '—')}</span>
    ),
  },
  { key: 'achievement', header: 'Achievement', render: (row) => row.achievement || '—' },
  {
    key: 'is_active',
    header: 'Status',
    render: (row) => (
      <Badge tone={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Showing' : 'Hidden'}</Badge>
    ),
  },
]

const FIELDS = [
  { name: 'full_name', label: 'Student name', required: true, placeholder: 'Ayesha Siddika' },
  { name: 'academic_year', label: 'Academic year', required: true, placeholder: '2025' },
  { name: 'student_class', label: 'Class', placeholder: 'Class 10' },
  { name: 'section', label: 'Section', placeholder: 'A' },
  { name: 'roll_number', label: 'Roll number', placeholder: '07' },
  { name: 'exam_name', label: 'Examination', placeholder: 'SSC' },
  { name: 'result', label: 'Result', placeholder: 'GPA 5.00', hint: 'Shown large on the card.' },
  { name: 'gpa', label: 'GPA', type: 'number', step: '0.01', min: 0, max: 5 },
  {
    name: 'achievement',
    label: 'Achievement',
    placeholder: 'Talentpool scholarship',
    fullWidth: true,
  },
  { name: 'photo', type: 'image', label: 'Photo', previewKey: 'photo_url', hint: 'A square portrait works best.' },
  { name: 'remarks', label: 'Remarks', type: 'textarea', rows: 3 },
  { name: 'order', label: 'Order within the year', type: 'number', min: 0, defaultValue: 0 },
  { name: 'is_featured', label: 'Feature at the top of the year', type: 'checkbox' },
  { name: 'is_active', label: 'Show on the website', type: 'checkbox', defaultValue: true },
]

/**
 * The public honour board.
 *
 * Kept apart from the student register on purpose: a student who left in 2019
 * still belongs here, and a name on this board need not have an enrolment
 * record behind it.
 */
export function SuccessfulStudentsAdmin() {
  const yearOptions = useMemo(() => recentYears(), [])

  return (
    <CrudPage
      title="Successful students"
      description="The results honour board shown publicly on the school's home page, filterable by year."
      service={successfulStudentService}
      module="achiever"
      singular="student"
      columns={COLUMNS}
      fields={FIELDS}
      filters={[{ name: 'academic_year', placeholder: 'All years', options: yearOptions }]}
      searchPlaceholder="Search by name, class or result…"
      emptyTitle="No results recorded yet"
      emptyDescription="Add the students whose results the school wants to celebrate."
    />
  )
}

export default SuccessfulStudentsAdmin
