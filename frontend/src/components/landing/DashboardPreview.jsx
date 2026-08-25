import { CalendarCheck, GraduationCap, Layers, Users } from 'lucide-react'

import { formatNumber, formatPercent } from '@/utils/formatters'

const ENROLMENT = [
  { label: 'C5', value: 68 },
  { label: 'C6', value: 82 },
  { label: 'C7', value: 74 },
  { label: 'C8', value: 91 },
  { label: 'C9', value: 86 },
  { label: 'C10', value: 63 },
]

const DONUT = [
  { label: 'Present', value: 88, color: '#059669' },
  { label: 'Late', value: 6, color: '#f5b324' },
  { label: 'Absent', value: 6, color: '#c8102e' },
]

function StatTile({ icon: Icon, label, value, tone, accent }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value}</p>
        </div>
        <span className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
      <p className={`mt-3 text-xs font-medium ${accent}`}>Updated in real time</p>
    </div>
  )
}

/** A stacked ring built from plain SVG — no chart library needed for three slices. */
function AttendanceDonut() {
  const radius = 52
  const circumference = 2 * Math.PI * radius

  // Each slice starts where the previous ones ended — derived up front so the
  // render stays a pure function of DONUT.
  const slices = DONUT.reduce((accumulated, slice) => {
    const previous = accumulated.at(-1)
    const length = (slice.value / 100) * circumference
    return [...accumulated, { ...slice, length, offset: previous ? previous.offset + previous.length : 0 }]
  }, [])

  return (
    <div className="flex items-center gap-6">
      <svg viewBox="0 0 140 140" className="h-36 w-36 shrink-0 -rotate-90" role="img" aria-label="Attendance breakdown">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="16" />
        {slices.map((slice) => (
          <circle
            key={slice.label}
            cx="70"
            cy="70"
            r={radius}
            fill="none"
            stroke={slice.color}
            strokeWidth="16"
            strokeDasharray={`${slice.length} ${circumference - slice.length}`}
            strokeDashoffset={-slice.offset}
            strokeLinecap="butt"
          />
        ))}
      </svg>

      <ul className="space-y-2.5">
        {DONUT.map((slice) => (
          <li key={slice.label} className="flex items-center gap-2.5 text-sm">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: slice.color }} />
            <span className="text-slate-600">{slice.label}</span>
            <span className="ml-auto font-semibold text-slate-900">{slice.value}%</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function DashboardPreview({ stats }) {
  return (
    <section id="about" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            The whole school, at a glance
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-slate-600">
            The dashboard every staff member lands on — shaped by the permissions their role carries.
          </p>
        </div>

        <div className="mt-14 overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 p-4 shadow-[var(--shadow-raised)] sm:p-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile
              icon={GraduationCap}
              label="Total Students"
              value={formatNumber(stats?.students ?? 1250)}
              tone="bg-brand-50 text-brand-600"
              accent="text-brand-600"
            />
            <StatTile
              icon={Users}
              label="Teachers"
              value={formatNumber(stats?.teachers ?? 85)}
              tone="bg-violet-50 text-violet-600"
              accent="text-violet-600"
            />
            <StatTile
              icon={Layers}
              label="Classes"
              value={formatNumber(stats?.classes ?? 42)}
              tone="bg-gold-50 text-gold-700"
              accent="text-gold-700"
            />
            <StatTile
              icon={CalendarCheck}
              label="Attendance"
              value={formatPercent(94.5)}
              tone="bg-emerald-50 text-emerald-600"
              accent="text-emerald-600"
            />
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-5">
            {/* Enrolment chart */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Enrolment by class</h3>
                <span className="text-xs text-slate-400">Current session</span>
              </div>
              <div className="mt-6 flex h-44 items-end gap-3" role="img" aria-label="Student count per class">
                {ENROLMENT.map((bar) => (
                  <div key={bar.label} className="flex flex-1 flex-col items-center gap-2">
                    <span className="text-[11px] font-semibold text-slate-500">{bar.value}</span>
                    <div className="flex w-full flex-1 items-end">
                      <div
                        className="w-full rounded-t-lg bg-gradient-to-t from-brand-700 via-brand-600 to-brand-400 transition-all"
                        style={{ height: `${bar.value}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-medium text-slate-400">{bar.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Attendance donut */}
            <div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-2">
              <h3 className="text-sm font-semibold text-slate-900">Today&rsquo;s attendance</h3>
              <div className="mt-5">
                <AttendanceDonut />
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default DashboardPreview
