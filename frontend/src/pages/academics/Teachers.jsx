import { useMemo } from 'react'

import Avatar from '@/components/ui/Avatar'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import CrudPage from '@/components/common/CrudPage'
import useApi from '@/hooks/useApi'
import { departmentService, designationService, teacherService } from '@/services'
import { formatDate } from '@/utils/formatters'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'on_leave', label: 'On leave' },
  { value: 'suspended', label: 'Suspended' },
  { value: 'resigned', label: 'Resigned' },
  { value: 'retired', label: 'Retired' },
]

const EMPLOYMENT_OPTIONS = [
  { value: 'full_time', label: 'Full time' },
  { value: 'part_time', label: 'Part time' },
  { value: 'contract', label: 'Contract' },
  { value: 'guest', label: 'Guest' },
]

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
]

export function Teachers() {
  const { data: designations } = useApi(() => designationService.all(), [], { initialData: [] })
  const { data: departments } = useApi(() => departmentService.all(), [], { initialData: [] })

  const designationOptions = useMemo(
    () => (designations ?? []).map((item) => ({ value: item.id, label: item.name })),
    [designations],
  )
  const departmentOptions = useMemo(
    () => (departments ?? []).map((item) => ({ value: item.id, label: item.name })),
    [departments],
  )

  const columns = [
    {
      key: 'full_name',
      header: 'Teacher',
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar src={row.photo_url} name={row.full_name} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-slate-900">{row.full_name}</p>
            <p className="font-mono text-xs text-slate-500">{row.employee_id}</p>
          </div>
        </div>
      ),
    },
    { key: 'designation_name', header: 'Designation', render: (row) => row.designation_name ?? '—' },
    { key: 'department_name', header: 'Department', render: (row) => row.department_name ?? '—' },
    {
      key: 'phone',
      header: 'Contact',
      render: (row) => (
        <div className="text-xs">
          <p className="text-slate-700">{row.phone || '—'}</p>
          <p className="text-slate-400">{row.email || ''}</p>
        </div>
      ),
    },
    { key: 'joining_date', header: 'Joined', render: (row) => formatDate(row.joining_date) },
    {
      key: 'employment_type',
      header: 'Type',
      render: (row) => <Badge tone="neutral">{row.employment_type?.replace('_', ' ')}</Badge>,
    },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} label={row.status_display} /> },
  ]

  // Memoised so the option lists are the only thing that rebuilds the field
  // list, matching how every other screen here declares its form.
  const fields = useMemo(
    () => [
      { name: 'full_name', label: 'Full name', required: true },
      { name: 'employee_id', label: 'Employee ID', required: true, unique: true },
      {
        name: 'email',
        label: 'Email',
        type: 'email',
        placeholder: 'teacher@holychildschool.edu.bd',
        hint: 'Signs in to the staff account created with this record.',
      },
      {
        name: 'phone',
        label: 'Phone',
        type: 'tel',
        placeholder: '+8801700000000',
        hint: 'Also the first password for that account — ask them to change it.',
      },
      { name: 'designation', label: 'Designation', type: 'select', options: designationOptions },
      { name: 'department', label: 'Department', type: 'select', options: departmentOptions },
      { name: 'employment_type', label: 'Employment type', type: 'select', options: EMPLOYMENT_OPTIONS, defaultValue: 'full_time' },
      { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, defaultValue: 'active' },
      { name: 'joining_date', label: 'Joining date', type: 'date' },
      { name: 'resignation_date', label: 'Resignation date', type: 'date' },
      { name: 'qualification', label: 'Qualification', placeholder: 'M.Sc. in Mathematics' },
      { name: 'specialization', label: 'Specialisation', placeholder: 'Algebra' },
      { name: 'experience_years', label: 'Years of experience', type: 'number', min: 0, defaultValue: 0 },
      { name: 'gender', label: 'Gender', type: 'select', options: GENDER_OPTIONS },
      { name: 'date_of_birth', label: 'Date of birth', type: 'date' },
      { name: 'blood_group', label: 'Blood group', placeholder: 'O+' },
      { name: 'national_id', label: 'National ID' },
      { name: 'address', label: 'Address', type: 'textarea' },
    ],
    [designationOptions, departmentOptions],
  )

  return (
    <CrudPage
      title="Teachers"
      description="The teaching staff register — designations, departments and employment records."
      service={teacherService}
      module="teacher"
      singular="teacher"
      columns={columns}
      fields={fields}
      createDefaults={teacherService.nextEmployeeId}
      checkUnique={teacherService.checkEmployeeId}
      searchPlaceholder="Search name, employee ID or phone…"
      filters={[
        { name: 'department', placeholder: 'All departments', options: departmentOptions },
        { name: 'status', placeholder: 'All statuses', options: STATUS_OPTIONS },
      ]}
      emptyTitle="No teachers found"
      emptyDescription="Add the first member of teaching staff to the register."
    />
  )
}

export default Teachers
