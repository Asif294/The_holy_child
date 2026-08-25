import {
  Award,
  BarChart3,
  BookOpen,
  CalendarCheck,
  GraduationCap,
  Layers,
  ShieldCheck,
  Users,
  Wallet,
} from 'lucide-react'

const FEATURES = [
  {
    icon: GraduationCap,
    title: 'Student Management',
    description: 'Admissions, enrolment records, guardians and the full student directory in one register.',
    tone: 'bg-brand-50 text-brand-600',
  },
  {
    icon: Users,
    title: 'Teacher Management',
    description: 'Staff records, designations, departments and subject assignments kept up to date.',
    tone: 'bg-violet-50 text-violet-600',
  },
  {
    icon: CalendarCheck,
    title: 'Attendance Tracking',
    description: 'Mark a whole section in one submission, then review daily and monthly attendance rates.',
    tone: 'bg-emerald-50 text-emerald-600',
  },
  {
    icon: Layers,
    title: 'Class Management',
    description: 'Classes, sections, class teachers and academic sessions from Play Group to Class 10.',
    tone: 'bg-sky-50 text-sky-600',
  },
  {
    icon: Wallet,
    title: 'Fee Management',
    description: 'Fee structures per class, invoices per student and payments reconciled automatically.',
    tone: 'bg-gold-50 text-gold-700',
  },
  {
    icon: Award,
    title: 'Exam Management',
    description: 'Exam routines, mark entry and results graded on the national scale, published on your word.',
    tone: 'bg-crimson-50 text-crimson-600',
  },
  {
    icon: ShieldCheck,
    title: 'Role-Based Access',
    description: 'Create roles, tick the permissions they carry, and every screen and API adapts instantly.',
    tone: 'bg-indigo-50 text-indigo-600',
  },
  {
    icon: BarChart3,
    title: 'Reports & Analytics',
    description: 'Enrolment, attendance and collection trends surfaced as charts you can act on.',
    tone: 'bg-teal-50 text-teal-600',
  },
]

export function Features() {
  return (
    <section id="features" className="bg-slate-50 py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-white px-3 py-1 text-xs font-semibold text-brand-700">
            <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
            Everything your school runs on
          </span>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            One platform for the whole school
          </h2>
          <p className="mt-4 text-lg leading-relaxed text-slate-600">
            From the first admission to the final result sheet — every module works from the same
            records, so nothing has to be entered twice.
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((feature) => (
            <article
              key={feature.title}
              className="group rounded-[var(--radius-card)] border border-slate-200 bg-white p-6 transition-all hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-[var(--shadow-float)]"
            >
              <span className={`inline-flex h-11 w-11 items-center justify-center rounded-xl ${feature.tone}`}>
                <feature.icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="mt-4 text-base font-semibold text-slate-900">{feature.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Features
