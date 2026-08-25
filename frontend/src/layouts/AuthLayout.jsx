import { Link, Outlet } from 'react-router-dom'
import { ArrowLeft, CheckCircle2 } from 'lucide-react'

import { Logo, LogoMark } from '@/components/common/Logo'
import useSchool from '@/hooks/useSchool'

const HIGHLIGHTS = [
  'Role-based access with granular permissions',
  'Attendance, exams and results in one place',
  'Fee invoicing and payment tracking',
  'Secure JWT authentication',
]

export function AuthLayout() {
  const { school } = useSchool()
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Form side */}
      <div className="flex flex-col px-5 py-8 sm:px-10">
        <div className="flex items-center justify-between">
          <Link to="/" className="min-w-0" aria-label={`Back to ${school.name_en}`}>
            <Logo primary="school" />
          </Link>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 transition-colors hover:text-brand-600"
          >
            <ArrowLeft className="h-4 w-4" /> Home
          </Link>
        </div>

        <div className="flex flex-1 items-center justify-center py-10">
          <div className="w-full max-w-md">
            <Outlet />
          </div>
        </div>

        <p className="text-center text-xs text-slate-400">
          © {new Date().getFullYear()} {school.name_en}. All rights reserved.
        </p>
      </div>

      {/* Brand side */}
      <div className="relative hidden overflow-hidden bg-brand-900 lg:flex lg:flex-col lg:justify-center lg:px-14">
        <div
          className="absolute inset-0 opacity-[0.07]"
          aria-hidden="true"
          style={{
            backgroundImage:
              'radial-gradient(circle at 20% 20%, white 1px, transparent 1px), radial-gradient(circle at 70% 60%, white 1px, transparent 1px)',
            backgroundSize: '48px 48px, 64px 64px',
          }}
        />
        <div className="absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand-600/40 blur-3xl" aria-hidden="true" />
        <div className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-gold-500/15 blur-3xl" aria-hidden="true" />

        <div className="relative">
          <LogoMark className="h-16 w-16" />
          <h2 className="mt-8 text-4xl font-extrabold leading-tight tracking-tight text-white">
            Smart School Management,
            <span className="block text-gold-400">Simplified.</span>
          </h2>
          <p className="mt-4 max-w-md text-base leading-relaxed text-brand-100">
            {school.name_en} — {school.address}. Serving {(school.grade_range || '').toLowerCase()} since {school.established}.
          </p>

          <ul className="mt-10 space-y-3.5">
            {HIGHLIGHTS.map((highlight) => (
              <li key={highlight} className="flex items-center gap-3 text-brand-50">
                <CheckCircle2 className="h-5 w-5 shrink-0 text-gold-400" aria-hidden="true" />
                <span className="text-sm">{highlight}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

export default AuthLayout
