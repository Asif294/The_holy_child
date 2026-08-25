import { useCallback, useMemo, useState } from 'react'
import { Eye, GraduationCap, Pencil, Plus, Search, Trash2 } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Select } from '@/components/ui/Input'
import Modal, { ConfirmDialog } from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import useUniqueCheck from '@/hooks/useUniqueCheck'
import { classService, guardianService, sectionService, sessionService, studentService } from '@/services'
import { formatDate } from '@/utils/formatters'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'graduated', label: 'Graduated' },
  { value: 'transferred', label: 'Transferred' },
  { value: 'dropped', label: 'Dropped out' },
  { value: 'suspended', label: 'Suspended' },
]

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
]

export function Students() {
  useDocumentTitle('Students')

  const toast = useToast()
  const list = usePaginatedList(studentService)

  const { data: classes } = useApi(() => classService.all(), [], { initialData: [] })
  const { data: sections } = useApi(() => sectionService.all(), [], { initialData: [] })
  const { data: sessions } = useApi(() => sessionService.all(), [], { initialData: [] })
  const { data: guardians } = useApi(() => guardianService.all(), [], { initialData: [] })

  const [editing, setEditing] = useState(null)
  const [viewing, setViewing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [isSaving, setSaving] = useState(false)
  const [isDeleting, setDeleting_] = useState(false)

  const classOptions = useMemo(() => (classes ?? []).map((c) => ({ value: c.id, label: c.name })), [classes])
  const sessionOptions = useMemo(() => (sessions ?? []).map((s) => ({ value: s.id, label: s.name })), [sessions])
  const guardianOptions = useMemo(
    () => (guardians ?? []).map((g) => ({ value: g.id, label: `${g.full_name} · ${g.phone}` })),
    [guardians],
  )

  // Sections are filtered to the class picked in the form, so a mismatched pair
  // can never be submitted in the first place.
  const [selectedClass, setSelectedClass] = useState('')
  const sectionOptions = useMemo(
    () =>
      (sections ?? [])
        .filter((section) => !selectedClass || String(section.school_class) === String(selectedClass))
        .map((section) => ({ value: section.id, label: `${section.class_name} — ${section.name}` })),
    [sections, selectedClass],
  )

  const fields = useMemo(
    () => [
      { name: 'full_name', label: 'Full name', required: true },
      { name: 'full_name_bn', label: 'Bangla name' },
      { name: 'student_id', label: 'Student ID', required: true },
      { name: 'admission_number', label: 'Admission number', required: true },
      { name: 'school_class', label: 'Class', type: 'select', options: classOptions },
      { name: 'section', label: 'Section', type: 'select', options: sectionOptions },
      { name: 'roll_number', label: 'Roll number', type: 'number', min: 1 },
      { name: 'session', label: 'Academic session', type: 'select', options: sessionOptions },
      { name: 'gender', label: 'Gender', type: 'select', options: GENDER_OPTIONS },
      { name: 'date_of_birth', label: 'Date of birth', type: 'date' },
      { name: 'blood_group', label: 'Blood group', placeholder: 'B+' },
      { name: 'religion', label: 'Religion' },
      { name: 'father_name', label: "Father's name" },
      { name: 'mother_name', label: "Mother's name" },
      { name: 'guardian', label: 'Guardian', type: 'select', options: guardianOptions },
      { name: 'emergency_contact', label: 'Emergency contact', type: 'tel' },
      { name: 'admission_date', label: 'Admission date', type: 'date' },
      { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, defaultValue: 'active' },
      { name: 'present_address', label: 'Present address', type: 'textarea' },
      { name: 'permanent_address', label: 'Permanent address', type: 'textarea' },
    ],
    [classOptions, sectionOptions, sessionOptions, guardianOptions],
  )

  // `editing` doubles as the form seed: the record when editing, and a fresh
  // `{}` when admitting. Handing over that new object — rather than a shared
  // `null` — re-seeds the form every time it opens, so cancelling a half-filled
  // admission and starting again begins from a blank form.
  const form = useResourceForm(fields, editing)

  // Both codes are pre-filled with a free number, but they can be typed over —
  // for a pupil transferring in with an ID already. This says so as it is typed
  // rather than leaving it to the save.
  const checkIdentifier = useUniqueCheck(studentService.checkIdentifiers, form.setErrors)

  const handleChange = useCallback(
    (name, value) => {
      form.change(name, value)

      if (name === 'student_id' || name === 'admission_number') {
        checkIdentifier(name, value, { exclude: editing?.id })
      }

      if (name === 'school_class') {
        setSelectedClass(value)
        form.change('section', '')
      }

      // A roll only means anything within a section, so picking one is what
      // decides the number — and picking a different one makes the old number
      // wrong, not just stale.
      if (name === 'section') fillNextRoll(value)
    },
    [form, checkIdentifier, editing],
  )

  /** Puts the next free roll in that section into the roll field. */
  async function fillNextRoll(sectionId) {
    if (!sectionId) return
    try {
      const { roll_number: roll } = await studentService.nextRoll(sectionId)
      form.setValues((current) => ({ ...current, roll_number: roll ?? '' }))
    } catch {
      // Not worth a toast — the field is editable, and the save checks the roll.
    }
  }

  /**
   * Opens a blank admission form, then fills in the student ID and admission
   * number the server will issue next. The modal opens straight away: the two
   * numbers arriving a moment later, or not at all, just leave fields to type
   * into, and the server re-checks whatever is finally submitted.
   */
  async function openCreate() {
    setSelectedClass('')
    setEditing({})
    try {
      const identifiers = await studentService.nextIdentifiers()
      form.setValues((current) => ({ ...current, ...identifiers }))
    } catch {
      // Not worth a toast — both fields are editable, so a clerk can type them.
    }
  }

  async function openEdit(row) {
    try {
      const detail = await studentService.retrieve(row.id)
      setSelectedClass(detail.school_class ?? '')
      setEditing(detail)
    } catch (error) {
      toast.error(error.message)
    }
  }

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = form.payload()
      if (editing?.id) {
        await studentService.patch(editing.id, payload)
        toast.success('Student updated.')
      } else {
        await studentService.create(payload)
        toast.success('Student admitted.')
      }
      setEditing(null)
      list.reload()
    } catch (error) {
      form.setErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    setDeleting_(true)
    try {
      await studentService.remove(deleting.id)
      toast.success('Student record removed.')
      setDeleting(null)
      list.reload()
    } catch (error) {
      toast.error(error.message)
    } finally {
      setDeleting_(false)
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'Student',
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar src={row.photo_url} name={row.full_name} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-slate-900">{row.full_name}</p>
            <p className="font-mono text-xs text-slate-500">{row.student_id}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'class_name',
      header: 'Class',
      render: (row) =>
        row.class_name ? (
          <span>
            {row.class_name}
            {row.section_name ? <span className="text-slate-400"> · {row.section_name}</span> : null}
          </span>
        ) : (
          '—'
        ),
    },
    { key: 'roll_number', header: 'Roll', render: (row) => row.roll_number ?? '—' },
    { key: 'gender', header: 'Gender', className: 'capitalize', render: (row) => row.gender || '—' },
    { key: 'admission_date', header: 'Admitted', render: (row) => formatDate(row.admission_date) },
    { key: 'status', header: 'Status', render: (row) => <StatusBadge status={row.status} label={row.status_display} /> },
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-28',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <button
            type="button"
            onClick={() => setViewing(row)}
            className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
            aria-label={`View ${row.full_name}`}
          >
            <Eye className="h-4 w-4" />
          </button>
          <Can permission="student.update">
            <button
              type="button"
              onClick={() => openEdit(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-brand-50 hover:text-brand-600"
              aria-label={`Edit ${row.full_name}`}
            >
              <Pencil className="h-4 w-4" />
            </button>
          </Can>
          <Can permission="student.delete">
            <button
              type="button"
              onClick={() => setDeleting(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-crimson-50 hover:text-crimson-600"
              aria-label={`Delete ${row.full_name}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </Can>
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Students"
        description="The student register — admissions, class placement and guardian details."
        actions={
          <Can permission="student.create">
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Admit student
            </Button>
          </Can>
        }
      />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={GraduationCap}
        emptyTitle="No students found"
        emptyDescription="Adjust your filters, or admit the first student."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search name, ID or admission no…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search students"
            />
            <Select
              className="w-auto min-w-[9rem]"
              placeholder="All classes"
              options={classOptions}
              value={list.filters.school_class ?? ''}
              onChange={(event) => list.setFilter('school_class', event.target.value)}
              aria-label="Filter by class"
            />
            <Select
              className="w-auto min-w-[9rem]"
              placeholder="All statuses"
              options={STATUS_OPTIONS}
              value={list.filters.status ?? ''}
              onChange={(event) => list.setFilter('status', event.target.value)}
              aria-label="Filter by status"
            />
            {list.search || Object.values(list.filters).some(Boolean) ? (
              <Button variant="ghost" size="sm" onClick={list.resetFilters}>
                Clear
              </Button>
            ) : null}
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

      {/* Create / edit */}
      <Modal
        isOpen={editing !== null}
        onClose={() => setEditing(null)}
        title={editing?.id ? 'Edit student' : 'Admit a student'}
        description={editing?.id ? editing.full_name : 'Enter the enrolment details for the new student.'}
        size="xl"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditing(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="student-form" isLoading={isSaving}>
              {editing?.id ? 'Save changes' : 'Admit student'}
            </Button>
          </div>
        }
      >
        <form id="student-form" onSubmit={handleSave} noValidate>
          <ResourceForm fields={fields} values={form.values} errors={form.errors} onChange={handleChange} />
        </form>
      </Modal>

      {/* Detail */}
      <Modal isOpen={Boolean(viewing)} onClose={() => setViewing(null)} title="Student details" size="md">
        {viewing ? (
          <div>
            <div className="flex items-center gap-4">
              <Avatar src={viewing.photo_url} name={viewing.full_name} size="lg" />
              <div>
                <p className="text-lg font-semibold text-slate-900">{viewing.full_name}</p>
                <p className="font-mono text-sm text-slate-500">{viewing.student_id}</p>
                <StatusBadge status={viewing.status} label={viewing.status_display} className="mt-1.5" />
              </div>
            </div>

            <dl className="mt-6 grid grid-cols-2 gap-x-4 gap-y-3.5 text-sm">
              {[
                ['Class', viewing.class_name ?? '—'],
                ['Section', viewing.section_name ?? '—'],
                ['Roll number', viewing.roll_number ?? '—'],
                ['Admission number', viewing.admission_number],
                ['Gender', viewing.gender || '—'],
                ['Admitted on', formatDate(viewing.admission_date)],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
                  <dd className="mt-0.5 capitalize text-slate-800">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        ) : null}
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title="Remove this student?"
        description={`${deleting?.full_name ?? ''} will be deactivated. Attendance, results and fee history are kept intact.`}
        confirmLabel="Remove student"
      />
    </div>
  )
}

export default Students
