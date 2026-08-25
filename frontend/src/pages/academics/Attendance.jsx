import { useCallback, useEffect, useMemo, useState } from 'react'
import { CalendarCheck, Save, Users } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input, { Select } from '@/components/ui/Input'
import { LoadingState } from '@/components/ui/Spinner'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import Can from '@/components/common/Can'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'
import { attendanceService, sectionService } from '@/services'
import { formatPercent } from '@/utils/formatters'

const STATUSES = [
  { value: 'present', label: 'Present', active: 'bg-emerald-600 text-white', idle: 'text-emerald-700 hover:bg-emerald-50' },
  { value: 'absent', label: 'Absent', active: 'bg-crimson-600 text-white', idle: 'text-crimson-700 hover:bg-crimson-50' },
  { value: 'late', label: 'Late', active: 'bg-gold-500 text-brand-950', idle: 'text-gold-700 hover:bg-gold-50' },
  { value: 'leave', label: 'Leave', active: 'bg-slate-600 text-white', idle: 'text-slate-600 hover:bg-slate-100' },
]

function today() {
  return new Date().toISOString().slice(0, 10)
}

export function Attendance() {
  useDocumentTitle('Attendance')

  const toast = useToast()
  const { data: sections } = useApi(() => sectionService.all(), [], { initialData: [] })

  const [sectionId, setSectionId] = useState('')
  const [date, setDate] = useState(today())
  const [roster, setRoster] = useState([])
  const [marks, setMarks] = useState({})
  const [isLoading, setLoading] = useState(false)
  const [isSaving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const sectionOptions = useMemo(
    () => (sections ?? []).map((section) => ({ value: section.id, label: `${section.class_name} — ${section.name}` })),
    [sections],
  )

  const loadRegister = useCallback(async () => {
    if (!sectionId) {
      setRoster([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await attendanceService.register(sectionId, date)
      setRoster(data.students ?? [])
      setMarks(
        Object.fromEntries(
          (data.students ?? []).map((student) => [student.student, student.status ?? 'present']),
        ),
      )
    } catch (caught) {
      setError(caught)
      setRoster([])
    } finally {
      setLoading(false)
    }
  }, [sectionId, date])

  useEffect(() => {
    loadRegister()
  }, [loadRegister])

  function setAll(status) {
    setMarks(Object.fromEntries(roster.map((student) => [student.student, status])))
  }

  async function handleSave() {
    setSaving(true)
    try {
      const result = await attendanceService.bulk({
        date,
        section: Number(sectionId),
        entries: roster.map((student) => ({ student: student.student, status: marks[student.student] ?? 'present' })),
      })
      toast.success(`Attendance saved — ${result.created} new, ${result.updated} updated.`)
      loadRegister()
    } catch (caught) {
      toast.error(caught.message)
    } finally {
      setSaving(false)
    }
  }

  const tally = useMemo(() => {
    const counts = { present: 0, absent: 0, late: 0, leave: 0 }
    for (const status of Object.values(marks)) {
      if (status in counts) counts[status] += 1
    }
    const counted = roster.length
    const attending = counts.present + counts.late
    return { ...counts, total: counted, rate: counted ? (attending / counted) * 100 : 0 }
  }, [marks, roster])

  return (
    <div>
      <PageHeader
        title="Attendance"
        description="Take a section's register for a date. Re-submitting the same date corrects the existing marks."
        actions={
          <Can permission="attendance.create">
            <Button
              leftIcon={<Save className="h-4 w-4" />}
              onClick={handleSave}
              isLoading={isSaving}
              disabled={!roster.length}
            >
              Save register
            </Button>
          </Can>
        }
      />

      <Card className="mb-4">
        <CardBody className="flex flex-wrap items-end gap-4">
          <Select
            label="Section"
            containerClassName="w-56"
            className="w-56"
            placeholder="Choose a section…"
            options={sectionOptions}
            value={sectionId}
            onChange={(event) => setSectionId(event.target.value)}
          />
          <Input
            label="Date"
            type="date"
            className="w-48"
            containerClassName="w-48"
            max={today()}
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />

          {roster.length > 0 ? (
            <div className="ml-auto flex flex-wrap items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Mark all:</span>
              {STATUSES.map((status) => (
                <Button key={status.value} variant="secondary" size="xs" onClick={() => setAll(status.value)}>
                  {status.label}
                </Button>
              ))}
            </div>
          ) : null}
        </CardBody>
      </Card>

      {roster.length > 0 ? (
        <div className="mb-4 grid gap-3 sm:grid-cols-5">
          {[
            { label: 'Students', value: tally.total, tone: 'brand' },
            { label: 'Present', value: tally.present, tone: 'success' },
            { label: 'Absent', value: tally.absent, tone: 'danger' },
            { label: 'Late', value: tally.late, tone: 'warning' },
            { label: 'Rate', value: formatPercent(tally.rate), tone: 'brand' },
          ].map((tile) => (
            <div key={tile.label} className="card p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{tile.label}</p>
              <p className="mt-1.5 text-xl font-bold text-slate-900">{tile.value}</p>
            </div>
          ))}
        </div>
      ) : null}

      <Card className="overflow-hidden">
        <CardHeader
          title="Register"
          description={sectionId ? `${roster.length} active students` : 'Select a section to begin.'}
          action={<CalendarCheck className="h-4 w-4 text-slate-400" aria-hidden="true" />}
        />

        {error ? (
          <div className="p-5">
            <Alert type="error" title="Could not load the register">
              {error.message}
            </Alert>
          </div>
        ) : isLoading ? (
          <LoadingState label="Loading the register…" />
        ) : !sectionId ? (
          <EmptyState
            icon={Users}
            title="No section selected"
            description="Choose a class section above to load its register for the chosen date."
          />
        ) : roster.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No students in this section"
            description="Admit students into this section before taking attendance."
          />
        ) : (
          <Table>
            <THead>
              <TR className="hover:bg-transparent">
                <TH className="w-16">Roll</TH>
                <TH>Student</TH>
                <TH className="w-24">Recorded</TH>
                <TH className="w-[22rem]">Status</TH>
              </TR>
            </THead>
            <TBody>
              {roster.map((student) => (
                <TR key={student.student}>
                  <TD className="font-medium text-slate-500">{student.roll_number ?? '—'}</TD>
                  <TD>
                    <p className="font-medium text-slate-900">{student.full_name}</p>
                    <p className="font-mono text-xs text-slate-400">{student.student_id}</p>
                  </TD>
                  <TD>
                    {student.status ? (
                      <Badge tone="neutral">Saved</Badge>
                    ) : (
                      <span className="text-xs text-slate-400">New</span>
                    )}
                  </TD>
                  <TD>
                    <div
                      role="radiogroup"
                      aria-label={`Attendance status for ${student.full_name}`}
                      className="inline-flex overflow-hidden rounded-lg border border-slate-200"
                    >
                      {STATUSES.map((status) => {
                        const isActive = (marks[student.student] ?? 'present') === status.value
                        return (
                          <button
                            key={status.value}
                            type="button"
                            role="radio"
                            aria-checked={isActive}
                            onClick={() =>
                              setMarks((current) => ({ ...current, [student.student]: status.value }))
                            }
                            className={`px-3 py-1.5 text-xs font-semibold transition-colors ${
                              isActive ? status.active : `bg-white ${status.idle}`
                            }`}
                          >
                            {status.label}
                          </button>
                        )
                      })}
                    </div>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        )}
      </Card>
    </div>
  )
}

export default Attendance
