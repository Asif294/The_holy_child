import { Compass, History, Target, Trophy } from 'lucide-react'

import SectionHeading from './SectionHeading'
import useSchool from '@/hooks/useSchool'

/**
 * "About the School" — story, history, mission, vision and achievements.
 *
 * Every paragraph is editable from the dashboard. Blank fields are dropped
 * rather than shown as empty cards, so a school that has only written its
 * mission still gets a section that looks deliberate.
 */
export function AboutSchool({ about }) {
  const { school } = useSchool()

  const pillars = [
    { key: 'history', icon: History, title: 'Our history', body: about?.history },
    { key: 'mission', icon: Target, title: 'Our mission', body: about?.mission },
    { key: 'vision', icon: Compass, title: 'Our vision', body: about?.vision },
  ].filter((pillar) => pillar.body)

  const achievements = about?.achievements ?? []

  return (
    <section id="about" className="bg-white py-20 sm:py-24">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionHeading
          eyebrow="About us"
          title={about?.headline || `About ${school.name_en}`}
          description={
            about?.summary ||
            `${school.name_en} has taught the children of ${school.address} since ${school.established}, from ${school.grade_range?.toLowerCase()}.`
          }
        />

        {about?.motto ? (
          <p className="mx-auto mt-6 max-w-2xl text-center text-lg font-semibold italic text-brand-700">
            “{about.motto}”
          </p>
        ) : null}

        {pillars.length ? (
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {pillars.map((pillar) => (
              <article
                key={pillar.key}
                className="rounded-2xl border border-slate-200 bg-white p-7 shadow-[var(--shadow-card)]"
              >
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <pillar.icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <h3 className="mt-5 text-lg font-semibold text-slate-900">{pillar.title}</h3>
                <p className="mt-2.5 whitespace-pre-line text-sm leading-relaxed text-slate-600">
                  {pillar.body}
                </p>
              </article>
            ))}
          </div>
        ) : null}

        {achievements.length ? (
          <div className="mt-16">
            <div className="flex items-center gap-3">
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-gold-100 text-gold-700">
                <Trophy className="h-4.5 w-4.5" aria-hidden="true" />
              </span>
              <h3 className="text-xl font-bold tracking-tight text-slate-900">Achievements</h3>
            </div>

            <ul className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {achievements.map((achievement) => (
                <li
                  key={achievement.id}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-colors hover:border-brand-200 hover:bg-brand-50/40"
                >
                  {achievement.metric ? (
                    <p className="text-3xl font-extrabold tracking-tight text-brand-700">{achievement.metric}</p>
                  ) : null}
                  <p className="mt-2 text-sm font-semibold text-slate-900">{achievement.title}</p>
                  {achievement.description ? (
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-500">{achievement.description}</p>
                  ) : null}
                  {achievement.year ? (
                    <p className="mt-3 text-[11px] font-semibold uppercase tracking-wide text-gold-700">
                      {achievement.year}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  )
}

export default AboutSchool
