import { Quote } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import SectionHeading from './SectionHeading'

/**
 * The Administration section: the principal and the vice principal.
 *
 * Each seat is independent — a school with no vice principal recorded shows
 * the principal alone rather than an empty placeholder, and a school with
 * neither hides the section entirely.
 */
export function Administration({ administration }) {
  const seats = [administration?.principal, administration?.vice_principal].filter(Boolean)
  if (!seats.length) return null

  return (
    <section id="administration" className="bg-slate-50 py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Administration"
          title="The people who run the school"
          description="Our principal and vice principal lead the academic and day-to-day life of the school."
        />

        <div className={`mt-14 grid gap-6 ${seats.length > 1 ? 'lg:grid-cols-2' : 'mx-auto max-w-3xl'}`}>
          {seats.map((person) => (
            <AdministratorCard key={person.id ?? person.office} person={person} />
          ))}
        </div>
      </div>
    </section>
  )
}

function AdministratorCard({ person }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[var(--shadow-card)]">
      <div className="flex flex-col items-center gap-4 bg-brand-900 px-6 py-8 text-center sm:flex-row sm:items-center sm:text-left">
        <Avatar
          src={person.photo_url}
          name={person.full_name}
          size="xl"
          className="shrink-0 ring-4 ring-gold-400/40"
        />
        <div className="min-w-0">
          <p className="text-lg font-semibold text-white">{person.full_name}</p>
          <p className="text-sm font-medium text-gold-400">{person.designation || person.office_display}</p>
          {person.qualification ? (
            <p className="mt-1 text-xs text-brand-200">{person.qualification}</p>
          ) : null}
          {person.experience_years ? (
            <p className="mt-1.5 text-xs text-brand-200">
              {person.experience_years} years in education
            </p>
          ) : null}
        </div>
      </div>

      <div className="px-6 py-7 sm:px-8">
        <Quote className="h-7 w-7 text-brand-200" aria-hidden="true" />
        <h3 className="mt-3 text-base font-semibold text-slate-900">
          Message from the {person.office_display || 'administration'}
        </h3>
        <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-slate-600">
          {person.message || person.biography || 'A message from this office will appear here soon.'}
        </p>
      </div>
    </article>
  )
}

export default Administration
