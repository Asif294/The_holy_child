import { Gauge, Layers3, Lock, MonitorSmartphone, ShieldCheck, Zap } from 'lucide-react'

const REASONS = [
  {
    icon: Lock,
    title: 'Secure',
    description: 'JWT authentication, hashed passwords and every permission re-checked on the server.',
  },
  {
    icon: Zap,
    title: 'Easy to Use',
    description: 'Clear screens your office staff can pick up on day one — no training manual required.',
  },
  {
    icon: ShieldCheck,
    title: 'Role-Based Access',
    description: 'Compose roles from granular permissions; staff see only what their job needs.',
  },
  {
    icon: Gauge,
    title: 'Real-Time Data',
    description: 'Attendance, fees and results reflected on the dashboard the moment they are recorded.',
  },
  {
    icon: Layers3,
    title: 'Scalable',
    description: 'Modular architecture — new modules and permissions slot in without a rewrite.',
  },
  {
    icon: MonitorSmartphone,
    title: 'Mobile Friendly',
    description: 'Works on the office desktop and on a teacher’s phone in the classroom.',
  },
]

export function WhyChooseUs() {
  return (
    <section className="bg-brand-900 py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">Why schools choose us</h2>
          <p className="mt-4 text-lg leading-relaxed text-brand-100">
            Built as production software, not a demo — with the security and structure a school&rsquo;s
            records deserve.
          </p>
        </div>

        <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {REASONS.map((reason) => (
            <article
              key={reason.title}
              className="rounded-[var(--radius-card)] border border-white/10 bg-white/[0.06] p-6 backdrop-blur-sm transition-colors hover:border-gold-400/40 hover:bg-white/10"
            >
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gold-400/15 text-gold-400">
                <reason.icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="mt-4 text-base font-semibold text-white">{reason.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-brand-100">{reason.description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}

export default WhyChooseUs
