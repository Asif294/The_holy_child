import { useMemo, useState } from 'react'
import { GraduationCap, Search, Users } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import cn from '@/utils/cn'
import SectionHeading from './SectionHeading'

const INITIAL_VISIBLE = 8

/**
 * The public staff directory.
 *
 * Filtering and searching happen in the browser: the whole directory is a
 * dozen or so cards, and a round trip per keystroke would be slower than the
 * work it saves. Managing the register itself is a permission-gated screen in
 * the dashboard — this is the visitor's view only.
 */
export function TeachersSection({ teachers = [] }) {
  const [query, setQuery] = useState('')
  const [department, setDepartment] = useState('all')
  const [showAll, setShowAll] = useState(false)

  const departments = useMemo(() => {
    const names = new Set()
    teachers.forEach((teacher) => {
      if (teacher.department_name) names.add(teacher.department_name)
    })
    return ['all', ...Array.from(names).sort()]
  }, [teachers])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return teachers.filter((teacher) => {
      if (department !== 'all' && teacher.department_name !== department) return false
      if (!needle) return true
      return [teacher.full_name, teacher.designation_name, teacher.specialization, ...(teacher.subject_names ?? [])]
        .filter(Boolean)
        .some((field) => field.toLowerCase().includes(needle))
    })
  }, [department, query, teachers])

  const visible = showAll ? filtered : filtered.slice(0, INITIAL_VISIBLE)

  if (!teachers.length) return null

  return (
    <section id="teachers" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="Our teachers"
          title="Meet the people who teach here"
          description={`${teachers.length} teachers across every class, most of whom have been with the school for years.`}
        />

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <Input
            containerClassName="w-full sm:max-w-xs"
            placeholder="Search by name or subject…"
            leftIcon={<Search className="h-4 w-4" />}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label="Search teachers"
          />

          {departments.length > 2 ? (
            <div className="flex flex-wrap justify-center gap-2">
              {departments.map((name) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => setDepartment(name)}
                  className={cn(
                    'rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors',
                    department === name
                      ? 'border-brand-600 bg-brand-600 text-white'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700',
                  )}
                >
                  {name === 'all' ? 'All departments' : name}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {visible.length ? (
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {visible.map((teacher) => (
              <li key={teacher.id}>
                <TeacherCard teacher={teacher} />
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            icon={Users}
            title="No teachers match that search"
            description="Try a different name, subject or department."
            className="mt-10"
          />
        )}

        {filtered.length > INITIAL_VISIBLE ? (
          <div className="mt-10 text-center">
            <button
              type="button"
              onClick={() => setShowAll((shown) => !shown)}
              className="inline-flex h-11 items-center rounded-lg border border-slate-300 px-5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
            >
              {showAll ? 'Show fewer teachers' : `Show all ${filtered.length} teachers`}
            </button>
          </div>
        ) : null}
      </div>
    </section>
  )
}

function TeacherCard({ teacher }) {
  return (
    <article className="group h-full rounded-2xl border border-slate-200 bg-white p-6 text-center transition-all hover:-translate-y-0.5 hover:border-brand-200 hover:shadow-[var(--shadow-float)]">
      <Avatar
        src={teacher.photo_url}
        name={teacher.full_name}
        size="xl"
        className="mx-auto ring-4 ring-brand-50 transition-colors group-hover:ring-brand-100"
      />
      <p className="mt-4 truncate text-base font-semibold text-slate-900">{teacher.full_name}</p>
      <p className="mt-0.5 text-sm font-medium text-brand-600">
        {teacher.designation_name || 'Teacher'}
      </p>

      {teacher.department_name ? (
        <p className="mt-2 text-xs text-slate-500">{teacher.department_name}</p>
      ) : null}

      {teacher.subject_names?.length ? (
        <div className="mt-3 flex flex-wrap justify-center gap-1.5">
          {teacher.subject_names.slice(0, 3).map((subject) => (
            <span
              key={subject}
              className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
            >
              {subject}
            </span>
          ))}
          {teacher.subject_names.length > 3 ? (
            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
              +{teacher.subject_names.length - 3}
            </span>
          ) : null}
        </div>
      ) : null}

      {teacher.qualification ? (
        <p className="mt-3 flex items-center justify-center gap-1.5 text-[11px] text-slate-500">
          <GraduationCap className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span className="truncate">{teacher.qualification}</span>
        </p>
      ) : null}
    </article>
  )
}

export default TeachersSection
