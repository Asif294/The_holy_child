import { Link } from 'react-router-dom'
import {
  ArrowRight,
  CalendarCheck,
  GraduationCap,
  Layers,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react'

import Button from '@/components/ui/Button'
import { formatNumber, formatPercent } from '@/utils/formatters'
import useSchool from '@/hooks/useSchool'

const BARS = [
  { label: 'Sat', value: 92 },
  { label: 'Sun', value: 96 },
  { label: 'Mon', value: 89 },
  { label: 'Tue', value: 94 },
  { label: 'Wed', value: 97 },
  { label: 'Thu', value: 91 },
]

/** The stat tiles inside the hero mock-up. */
function MiniStat({ icon: Icon, label, value, tone }) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3.5">
      <div className="flex items-center justify-between">
        <span className={`inline-flex h-8 w-8 items-center justify-center rounded-lg ${tone}`}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </span>
        <TrendingUp className="h-3.5 w-3.5 text-emerald-500" aria-hidden="true" />
      </div>
      <p className="mt-2.5 text-xl font-bold tracking-tight text-slate-900">{value}</p>
      <p className="text-[11px] font-medium text-slate-500">{label}</p>
    </div>
  )
}

export function Hero({ stats }) {
  const { school } = useSchool()
  const students = stats?.students ?? 1250
  const teachers = stats?.teachers ?? 85
  const classes = stats?.classes ?? 42

  return (
    <section id="home" className="relative overflow-hidden bg-white pt-16">
      {/* Ambient background */}
      <div
        className="absolute inset-x-0 top-0 h-[36rem] bg-gradient-to-b from-brand-50 via-white to-white"
        aria-hidden="true"
      />
      <div
        className="absolute -right-40 top-10 h-96 w-96 rounded-full bg-brand-200/40 blur-3xl"
        aria-hidden="true"
      />
      <div
        className="absolute -left-32 top-64 h-80 w-80 rounded-full bg-gold-200/40 blur-3xl"
        aria-hidden="true"
      />

      <div className="relative mx-auto grid max-w-7xl items-center gap-14 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:gap-10 lg:px-8 lg:py-24">
        {/* Copy */}
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            Trusted since {school.established} · {school.address}
          </span>

          <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
            Smart School Management,
            <span className="block text-brand-600">Simplified.</span>
          </h1>

          <p className="mt-5 max-w-xl text-lg leading-relaxed text-slate-600">
            Manage students, teachers, attendance, classes, fees and academic activities from one
            powerful platform — built for {school.name_en}.
          </p>

          <p className="font-bangla mt-3 text-base text-slate-500" lang="bn">
            {school.name_bn} · {school.grade_range_bn}
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/register">
              <Button size="lg" rightIcon={<ArrowRight className="h-4 w-4" />}>
                Get Started
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="secondary">
                Explore Features
              </Button>
            </a>
          </div>

          <dl className="mt-10 grid max-w-lg grid-cols-3 gap-6 border-t border-slate-200 pt-7">
            {[
              { label: 'Students', value: formatNumber(students) },
              { label: 'Teachers', value: formatNumber(teachers) },
              { label: 'Classes', value: formatNumber(classes) },
            ].map((stat) => (
              <div key={stat.label}>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">{stat.label}</dt>
                <dd className="mt-1 text-2xl font-bold tracking-tight text-slate-900">{stat.value}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Dashboard mock-up */}
        <div className="relative">
          <div className="absolute -inset-4 rounded-3xl bg-gradient-to-tr from-brand-600/10 via-transparent to-gold-400/20 blur-2xl" aria-hidden="true" />

          <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-[var(--shadow-float)]">
            {/* Window chrome */}
            <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-crimson-400" />
              <span className="h-2.5 w-2.5 rounded-full bg-gold-400" />
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
              <span className="ml-3 truncate text-xs font-medium text-slate-400">
                smartschool · dashboard
              </span>
            </div>

            <div className="p-4">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <MiniStat icon={GraduationCap} label="Total Students" value={formatNumber(students)} tone="bg-brand-50 text-brand-600" />
                <MiniStat icon={Users} label="Teachers" value={formatNumber(teachers)} tone="bg-violet-50 text-violet-600" />
                <MiniStat icon={Layers} label="Classes" value={formatNumber(classes)} tone="bg-gold-50 text-gold-700" />
                <MiniStat icon={CalendarCheck} label="Attendance" value={formatPercent(94.5)} tone="bg-emerald-50 text-emerald-600" />
              </div>

              {/* Attendance chart */}
              <div className="mt-3 rounded-xl border border-slate-100 bg-white p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-800">Weekly Attendance</p>
                  <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                    +2.4%
                  </span>
                </div>
                <div className="mt-4 flex h-28 items-end gap-2.5" role="img" aria-label="Weekly attendance rate by day">
                  {BARS.map((bar) => (
                    <div key={bar.label} className="flex flex-1 flex-col items-center gap-1.5">
                      <div className="flex w-full flex-1 items-end">
                        <div
                          className="w-full rounded-t-md bg-gradient-to-t from-brand-600 to-brand-400"
                          style={{ height: `${bar.value}%` }}
                        />
                      </div>
                      <span className="text-[10px] font-medium text-slate-400">{bar.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Fee progress */}
              <div className="mt-3 rounded-xl border border-slate-100 bg-white p-4">
                <div className="flex items-center justify-between text-sm">
                  <p className="font-semibold text-slate-800">Fee Collection</p>
                  <p className="font-semibold text-slate-900">78%</p>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full w-[78%] rounded-full bg-gradient-to-r from-gold-400 to-gold-600" />
                </div>
                <div className="mt-2.5 flex justify-between text-[11px] text-slate-500">
                  <span>Collected ৳4,86,000</span>
                  <span>Pending ৳1,37,000</span>
                </div>
              </div>
            </div>
          </div>

          {/* Floating badge */}
          <div className="absolute -bottom-5 -left-4 hidden items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-[var(--shadow-float)] sm:flex">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <CalendarCheck className="h-4.5 w-4.5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">Attendance recorded</p>
              <p className="text-[11px] text-slate-500">Class 9 — Section A · just now</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Hero
