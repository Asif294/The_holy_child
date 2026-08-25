import { Link } from 'react-router-dom'
import {
  Activity,
  CalendarCheck,
  CalendarDays,
  ClipboardList,
  CreditCard,
  GraduationCap,
  Layers,
  Megaphone,
  Users,
  Wallet,
} from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import StatCard from '@/components/dashboard/StatCard'
import {
  AttendanceBreakdownChart,
  AttendanceTrendChart,
  EnrollmentChart,
  FeeTrendChart,
} from '@/components/dashboard/Charts'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import { dashboardService } from '@/services'
import { formatCurrency, formatDate, formatNumber, formatPercent, formatRelative } from '@/utils/formatters'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function Dashboard() {
  useDocumentTitle('Dashboard')

  const { user } = useAuth()
  const { data, error, isLoading } = useApi(() => dashboardService.overview(), [])

  const summary = data?.summary ?? {}
  const attendanceBreakdown = [
    { name: 'Present', value: summary.todays_present ?? 0 },
    { name: 'Absent', value: summary.todays_absent ?? 0 },
  ]
  const hasAttendanceToday = attendanceBreakdown.some((slice) => slice.value > 0)

  return (
    <div>
      <PageHeader
        title={`${greeting()}, ${(user?.full_name ?? user?.name ?? '').split(' ')[0] || 'there'}`}
        description={`Here is what is happening at the school today, ${formatDate(new Date())}.`}
      />

      {error ? (
        <Alert type="error" title="Could not load the dashboard" className="mb-6">
          {error.message}
        </Alert>
      ) : null}

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          icon={GraduationCap}
          label="Total Students"
          value={formatNumber(summary.total_students)}
          hint="Actively enrolled"
          tone="brand"
          isLoading={isLoading}
        />
        <StatCard
          icon={Users}
          label="Total Teachers"
          value={formatNumber(summary.total_teachers)}
          hint="On active duty"
          tone="violet"
          isLoading={isLoading}
        />
        <StatCard
          icon={Layers}
          label="Total Classes"
          value={formatNumber(summary.total_classes)}
          hint={`${formatNumber(summary.total_subjects)} subjects offered`}
          tone="sky"
          isLoading={isLoading}
        />
        <StatCard
          icon={CalendarCheck}
          label="Today's Attendance"
          value={formatPercent(summary.todays_attendance_rate)}
          hint={`${formatNumber(summary.todays_present)} present · ${formatNumber(summary.todays_absent)} absent`}
          tone="emerald"
          isLoading={isLoading}
        />
        <StatCard
          icon={Wallet}
          label="Pending Fees"
          value={formatCurrency(summary.pending_fees)}
          hint={`${formatCurrency(summary.collected_fees)} collected`}
          tone="gold"
          isLoading={isLoading}
        />
        <StatCard
          icon={ClipboardList}
          label="Upcoming Exams"
          value={formatNumber(summary.upcoming_exams)}
          hint={`${formatNumber(summary.pending_approvals)} approvals pending`}
          tone="crimson"
          isLoading={isLoading}
        />
      </div>

      {/* Charts */}
      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Attendance trend" description="Daily attendance rate over the last seven days" />
          <CardBody className="pt-2">
            {isLoading ? (
              <div className="skeleton h-[260px] w-full" />
            ) : (
              <AttendanceTrendChart data={data?.attendance_trend ?? []} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Today's attendance" description="Present against absent" />
          <CardBody className="pt-2">
            {isLoading ? (
              <div className="skeleton h-[240px] w-full" />
            ) : hasAttendanceToday ? (
              <AttendanceBreakdownChart data={attendanceBreakdown} />
            ) : (
              <EmptyState
                icon={CalendarCheck}
                title="No register submitted yet"
                description="Attendance for today has not been recorded."
                className="py-12"
              />
            )}
          </CardBody>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader title="Enrolment by class" description="Active students per class" />
          <CardBody className="pt-2">
            {isLoading ? (
              <div className="skeleton h-[260px] w-full" />
            ) : (
              <EnrollmentChart data={data?.enrollment_by_class ?? []} />
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Fee collection" description="Collected per month" />
          <CardBody className="pt-2">
            {isLoading ? <div className="skeleton h-[240px] w-full" /> : <FeeTrendChart data={data?.fee_trend ?? []} />}
          </CardBody>
        </Card>
      </div>

      {/* Feeds */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader
            title="Recent activity"
            action={<Activity className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <ul className="divide-y divide-slate-100">
            {(data?.recent_activities ?? []).length === 0 ? (
              <li>
                <EmptyState icon={Activity} title="No activity yet" className="py-10" />
              </li>
            ) : (
              (data?.recent_activities ?? []).map((activity) => (
                <li key={activity.id} className="flex gap-3 px-5 py-3.5">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-500" aria-hidden="true" />
                  <div className="min-w-0">
                    <p className="text-sm text-slate-700">{activity.description}</p>
                    <p className="mt-0.5 text-xs text-slate-400">
                      {activity.actor_display} · {formatRelative(activity.created_at)}
                    </p>
                  </div>
                </li>
              ))
            )}
          </ul>
        </Card>

        <Card>
          <CardHeader
            title="Upcoming events"
            action={
              <Link to="/app/notices" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                All
              </Link>
            }
          />
          <ul className="divide-y divide-slate-100">
            {(data?.upcoming_events ?? []).length === 0 ? (
              <li>
                <EmptyState icon={CalendarDays} title="Nothing scheduled" className="py-10" />
              </li>
            ) : (
              (data?.upcoming_events ?? []).map((event) => (
                <li key={event.id} className="flex items-start gap-3 px-5 py-3.5">
                  <span className="flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg bg-brand-50 text-brand-700">
                    <span className="text-sm font-bold leading-none">{new Date(event.start_date).getDate()}</span>
                    <span className="text-[10px] uppercase leading-none">
                      {new Date(event.start_date).toLocaleString('en', { month: 'short' })}
                    </span>
                  </span>
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-800">{event.title}</p>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {event.category_display}
                      {event.venue ? ` · ${event.venue}` : ''}
                    </p>
                  </div>
                </li>
              ))
            )}
          </ul>
        </Card>

        <Card>
          <CardHeader
            title="Recent payments"
            action={
              <Link to="/app/payments" className="text-sm font-medium text-brand-600 hover:text-brand-700">
                All
              </Link>
            }
          />
          <ul className="divide-y divide-slate-100">
            {(data?.recent_payments ?? []).length === 0 ? (
              <li>
                <EmptyState icon={CreditCard} title="No payments recorded" className="py-10" />
              </li>
            ) : (
              (data?.recent_payments ?? []).map((payment) => (
                <li key={payment.id} className="flex items-center gap-3 px-5 py-3.5">
                  <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                    <CreditCard className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">{payment.student_name}</p>
                    <p className="text-xs text-slate-500">
                      {payment.receipt_number} · {payment.method_display}
                    </p>
                  </div>
                  <span className="shrink-0 text-sm font-semibold text-slate-900">
                    {formatCurrency(payment.amount)}
                  </span>
                </li>
              ))
            )}
          </ul>
        </Card>
      </div>

      {/* Notices */}
      {(data?.recent_notices ?? []).length > 0 ? (
        <Card className="mt-4">
          <CardHeader
            title="Latest notices"
            action={<Megaphone className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <ul className="divide-y divide-slate-100">
            {data.recent_notices.map((notice) => (
              <li key={notice.id} className="flex flex-wrap items-start justify-between gap-3 px-5 py-3.5">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800">{notice.title}</p>
                  <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{notice.body}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <StatusBadge status={notice.priority} label={notice.priority_display} />
                  <Badge tone="neutral">{formatDate(notice.published_at)}</Badge>
                </div>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </div>
  )
}

export default Dashboard
