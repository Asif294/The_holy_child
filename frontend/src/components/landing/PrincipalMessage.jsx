import { Quote } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import useSchool from '@/hooks/useSchool'

/** Rendered from the public principal endpoint; hidden when no record exists. */
export function PrincipalMessage({ principal }) {
  const { school } = useSchool()
  if (!principal) return null

  return (
    <section className="bg-slate-50 py-20 sm:py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[var(--shadow-card)] md:grid md:grid-cols-3">
          <div className="flex flex-col items-center justify-center gap-4 bg-brand-900 px-6 py-10 text-center">
            <Avatar
              src={principal.photo_url}
              name={principal.full_name}
              size="xl"
              className="ring-4 ring-gold-400/40"
            />
            <div>
              <p className="text-lg font-semibold text-white">{principal.full_name}</p>
              <p className="text-sm text-gold-400">{principal.designation}</p>
              {principal.qualification ? (
                <p className="mt-1 text-xs text-brand-200">{principal.qualification}</p>
              ) : null}
              {principal.experience_years ? (
                <p className="mt-2 text-xs text-brand-200">
                  {principal.experience_years} years in education
                </p>
              ) : null}
            </div>
          </div>

          <div className="px-6 py-10 sm:px-10 md:col-span-2">
            <Quote className="h-8 w-8 text-brand-200" aria-hidden="true" />
            <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
              Message from the Principal
            </h2>
            <p className="mt-4 whitespace-pre-line text-base leading-relaxed text-slate-600">
              {principal.message || `Welcome to ${school.name_en}.`}
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

export default PrincipalMessage
