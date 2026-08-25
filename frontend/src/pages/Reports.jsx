import { useState } from 'react'
import { Download, GraduationCap, Wallet } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import { LoadingState } from '@/components/ui/Spinner'
import { Table, TBody, TD, TH, THead, TR } from '@/components/ui/Table'
import Can from '@/components/common/Can'
import PageHeader from '@/components/common/PageHeader'
import { AttendanceTrendChart, EnrollmentChart, FeeTrendChart } from '@/components/dashboard/Charts'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'
import { dashboardService, invoiceService, studentService } from '@/services'
import { formatCurrency, formatNumber, formatPercent, humanise } from '@/utils/formatters'

/** Client-side CSV export — nothing here leaves the browser. */
function downloadCsv(filename, rows) {
  const csv = rows
    .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function Reports() {
  useDocumentTitle('Reports')

  const toast = useToast()
  const [days, setDays] = useState(30)

  const { data: studentStats, isLoading: studentsLoading } = useApi(() => studentService.statistics(), [])
  const { data: feeStats, isLoading: feesLoading } = useApi(() => invoiceService.statistics(), [])
  const { data: enrolment, isLoading: enrolmentLoading } = useApi(() => dashboardService.enrollment(), [], {
    initialData: [],
  })
  const { data: attendance, isLoading: attendanceLoading } = useApi(
    () => dashboardService.attendanceTrend(days),
    [days],
    { initialData: [] },
  )
  const { data: feeTrend, isLoading: feeTrendLoading } = useApi(() => dashboardService.feeTrend(12), [], {
    initialData: [],
  })

  function exportEnrolment() {
    downloadCsv('enrolment-by-class.csv', [
      ['Class', 'Students'],
      ...(enrolment ?? []).map((row) => [row.class_name, row.students]),
    ])
    toast.success('Enrolment report exported.')
  }

  function exportAttendance() {
    downloadCsv(`attendance-last-${days}-days.csv`, [
      ['Date', 'Present', 'Absent', 'Rate (%)'],
      ...(attendance ?? []).map((row) => [row.date, row.present, row.absent, row.rate]),
    ])
    toast.success('Attendance report exported.')
  }

  return (
    <div>
      <PageHeader
        title="Reports"
        description="Enrolment, attendance and fee-collection trends across the school."
        actions={
          <Can permission="report.export">
            <Button variant="secondary" leftIcon={<Download className="h-4 w-4" />} onClick={exportEnrolment}>
              Export enrolment
            </Button>
          </Can>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Enrolment */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Enrolment by class"
            description="Active students per class in the current session"
            action={<GraduationCap className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <CardBody className="pt-2">
            {enrolmentLoading ? <div className="skeleton h-[260px] w-full" /> : <EnrollmentChart data={enrolment} />}
          </CardBody>
        </Card>

        {/* Student breakdown */}
        <Card>
          <CardHeader title="Student breakdown" />
          <CardBody>
            {studentsLoading ? (
              <LoadingState />
            ) : (
              <dl className="space-y-3.5 text-sm">
                {[
                  ['Total enrolled', formatNumber(studentStats?.total)],
                  ['Active', formatNumber(studentStats?.active)],
                  ['Male', formatNumber(studentStats?.male)],
                  ['Female', formatNumber(studentStats?.female)],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                    <dt className="text-slate-500">{label}</dt>
                    <dd className="font-semibold text-slate-900">{value}</dd>
                  </div>
                ))}
              </dl>
            )}
          </CardBody>
        </Card>
      </div>

      {/* Attendance */}
      <Card className="mt-4">
        <CardHeader
          title="Attendance trend"
          description={`Daily attendance rate over the last ${days} days`}
          action={
            <div className="flex items-center gap-2">
              {[7, 30, 90].map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setDays(option)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                    days === option ? 'bg-brand-600 text-white' : 'text-slate-500 hover:bg-slate-100'
                  }`}
                >
                  {option}d
                </button>
              ))}
              <Can permission="report.export">
                <Button variant="ghost" size="xs" leftIcon={<Download className="h-3.5 w-3.5" />} onClick={exportAttendance}>
                  Export
                </Button>
              </Can>
            </div>
          }
        />
        <CardBody className="pt-2">
          {attendanceLoading ? (
            <div className="skeleton h-[260px] w-full" />
          ) : (
            <AttendanceTrendChart data={attendance} />
          )}
        </CardBody>
      </Card>

      {/* Finance */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Fee collection"
            description="Collected per month over the last year"
            action={<Wallet className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <CardBody className="pt-2">
            {feeTrendLoading ? <div className="skeleton h-[240px] w-full" /> : <FeeTrendChart data={feeTrend} />}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Collection summary" />
          <CardBody>
            {feesLoading ? (
              <LoadingState />
            ) : (
              <>
                <dl className="space-y-3.5 text-sm">
                  {[
                    ['Total billed', formatCurrency(feeStats?.total_billed)],
                    ['Collected', formatCurrency(feeStats?.total_collected)],
                    ['Outstanding', formatCurrency(feeStats?.total_outstanding)],
                    ['Collection rate', formatPercent(feeStats?.collection_rate)],
                    ['Overdue invoices', formatNumber(feeStats?.overdue_count)],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                      <dt className="text-slate-500">{label}</dt>
                      <dd className="font-semibold text-slate-900">{value}</dd>
                    </div>
                  ))}
                </dl>

                {feeStats?.by_status?.length ? (
                  <Table className="mt-5 min-w-0">
                    <THead>
                      <TR className="hover:bg-transparent">
                        <TH className="px-0">Status</TH>
                        <TH className="px-0 text-right">Invoices</TH>
                      </TR>
                    </THead>
                    <TBody>
                      {feeStats.by_status.map((row) => (
                        <TR key={row.status}>
                          <TD className="px-0">{humanise(row.status)}</TD>
                          <TD className="px-0 text-right font-medium">{row.total}</TD>
                        </TR>
                      ))}
                    </TBody>
                  </Table>
                ) : null}
              </>
            )}
          </CardBody>
        </Card>
      </div>

      <Alert type="info" className="mt-5">
        Exports are generated in your browser from the data currently on screen — nothing is sent anywhere.
        Exporting requires the <span className="font-mono text-xs">report.export</span> permission.
      </Alert>
    </div>
  )
}

export default Reports
