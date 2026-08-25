import { useEffect, useMemo, useState } from 'react'
import { Award, Medal, Star } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import EmptyState from '@/components/ui/EmptyState'
import { Spinner } from '@/components/ui/Spinner'
import cn from '@/utils/cn'
import { publicSiteService } from '@/services'
import SectionHeading from './SectionHeading'

/**
 * The results honour board, filtered by academic year.
 *
 * The year filter re-queries rather than filtering in memory: an honour board
 * grows every year and there is no reason to ship a decade of it to a visitor
 * who wants to see this year's SSC results.
 */
export function SuccessfulStudents({ years = [], initialStudents = [] }) {
  const [year, setYear] = useState('all')
  const [students, setStudents] = useState(initialStudents)
  const [isLoading, setLoading] = useState(false)

  useEffect(() => {
    // The unfiltered list arrives with the page; only a real filter needs a call.
    if (year === 'all') {
      setStudents(initialStudents)
      return undefined
    }

    let cancelled = false
    setLoading(true)
    publicSiteService
      .successfulStudents(year)
      .then((rows) => {
        if (!cancelled) setStudents(rows)
      })
      .catch(() => {
        if (!cancelled) setStudents([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [initialStudents, year])

  const options = useMemo(() => ['all', ...years], [years])
  const featured = students.filter((student) => student.is_featured)
  const rest = students.filter((student) => !student.is_featured)

  if (!initialStudents.length && !years.length) return null

  return (
    <section id="results" className="bg-brand-950 py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          tone="dark"
          eyebrow="Successful students"
          title="Results worth celebrating"
          description="The students whose examination results and achievements the school is proudest of."
        />

        {options.length > 1 ? (
          <div className="mt-10 flex flex-wrap items-center justify-center gap-2" role="group" aria-label="Filter by academic year">
            {options.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setYear(option)}
                aria-pressed={year === option}
                className={cn(
                  'rounded-full border px-4 py-1.5 text-sm font-semibold transition-colors',
                  year === option
                    ? 'border-gold-400 bg-gold-500 text-brand-950'
                    : 'border-white/20 bg-white/5 text-brand-100 hover:border-white/40 hover:text-white',
                )}
              >
                {option === 'all' ? 'All years' : option}
              </button>
            ))}
          </div>
        ) : null}

        {isLoading ? (
          <div className="mt-14 flex justify-center">
            <Spinner className="text-gold-400" label="Loading results" />
          </div>
        ) : students.length ? (
          <>
            {featured.length ? (
              <ul className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {featured.map((student) => (
                  <li key={student.id}>
                    <FeaturedCard student={student} />
                  </li>
                ))}
              </ul>
            ) : null}

            {rest.length ? (
              <ul
                className={cn(
                  'grid gap-4 sm:grid-cols-2 lg:grid-cols-4',
                  featured.length ? 'mt-5' : 'mt-12',
                )}
              >
                {rest.map((student) => (
                  <li key={student.id}>
                    <ResultCard student={student} />
                  </li>
                ))}
              </ul>
            ) : null}
          </>
        ) : (
          <div className="mt-12 rounded-2xl border border-white/10 bg-white/5 py-4">
            <EmptyState
              icon={Award}
              title="Nothing recorded for this year yet"
              description="Choose another year, or check back after the next results are published."
              className="text-brand-100 [&_h3]:text-white [&_p]:text-brand-200"
            />
          </div>
        )}
      </div>
    </section>
  )
}

/** The pinned students — bigger card, gold trim. */
function FeaturedCard({ student }) {
  return (
    <article className="h-full rounded-2xl border border-gold-400/30 bg-gradient-to-br from-white/[0.08] to-white/[0.02] p-6 backdrop-blur">
      <div className="flex items-start gap-4">
        <Avatar
          src={student.photo_url}
          name={student.full_name}
          size="lg"
          className="shrink-0 ring-2 ring-gold-400/50"
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Star className="h-3.5 w-3.5 shrink-0 fill-gold-400 text-gold-400" aria-hidden="true" />
            <span className="text-[11px] font-semibold uppercase tracking-wide text-gold-300">
              {student.academic_year}
            </span>
          </div>
          <p className="mt-1 truncate text-lg font-bold text-white">{student.full_name}</p>
          <p className="text-sm text-brand-200">
            {[student.student_class, student.section && `Section ${student.section}`]
              .filter(Boolean)
              .join(' · ') || '—'}
          </p>
        </div>
      </div>

      <div className="mt-5 flex items-end justify-between gap-3 border-t border-white/10 pt-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-brand-300">
            {student.exam_name || 'Result'}
          </p>
          <p className="mt-1 text-2xl font-extrabold tracking-tight text-gold-400">
            {student.result || (student.gpa ? `GPA ${student.gpa}` : '—')}
          </p>
        </div>
        {student.achievement ? (
          <span className="rounded-lg bg-gold-500/15 px-2.5 py-1 text-right text-[11px] font-semibold text-gold-300">
            {student.achievement}
          </span>
        ) : null}
      </div>

      {student.remarks ? (
        <p className="mt-4 text-xs leading-relaxed text-brand-200">{student.remarks}</p>
      ) : null}
    </article>
  )
}

/** Everyone else — compact row-sized card. */
function ResultCard({ student }) {
  return (
    <article className="flex h-full items-center gap-3.5 rounded-xl border border-white/10 bg-white/[0.04] p-4">
      <Avatar src={student.photo_url} name={student.full_name} size="md" className="shrink-0" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-white">{student.full_name}</p>
        <p className="truncate text-xs text-brand-300">
          {[student.student_class, student.exam_name, student.academic_year].filter(Boolean).join(' · ')}
        </p>
        <p className="mt-1.5 inline-flex items-center gap-1.5 text-sm font-bold text-gold-400">
          <Medal className="h-3.5 w-3.5" aria-hidden="true" />
          {student.result || (student.gpa ? `GPA ${student.gpa}` : '—')}
        </p>
      </div>
    </article>
  )
}

export default SuccessfulStudents
