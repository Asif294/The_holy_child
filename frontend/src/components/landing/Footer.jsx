import { Link } from 'react-router-dom'
import { Mail, MapPin, MessageCircle, Phone } from 'lucide-react'

import { LogoMark } from '@/components/common/Logo'
import useSchool from '@/hooks/useSchool'

const COLUMNS = [
  {
    title: 'The school',
    links: [
      { label: 'About us', href: '#about' },
      { label: 'Administration', href: '#administration' },
      { label: 'Our teachers', href: '#teachers' },
      { label: 'Successful students', href: '#results' },
    ],
  },
  {
    title: 'Visit',
    links: [
      { label: 'Contact', href: '#contact' },
      { label: 'Admissions', href: '#contact' },
      { label: 'Notices', href: '#contact' },
    ],
  },
  {
    // Staff only. Accounts are issued by the office, so there is nothing to
    // link a visitor to here beyond the sign-in page itself.
    title: 'Staff',
    links: [{ label: 'Admin sign-in', to: '/login' }],
  },
]

// Who to reach about the site itself, as opposed to the school. The number is
// written the way it is dialled locally and linked the way WhatsApp needs it.
const DEVELOPER = {
  name: 'Asifur Rahman',
  phone: '01885430525',
  whatsapp: 'https://wa.me/8801885430525',
}

export function Footer() {
  const { school } = useSchool()
  return (
    <footer id="contact" className="bg-brand-950 text-brand-100">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="grid gap-10 lg:grid-cols-5">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-3">
              <LogoMark className="h-11 w-11" />
              <div className="min-w-0">
                {/* The school's own name leads here too — `brand_name` is the
                    product wordmark and belongs in the dashboard, not on the
                    school's front page. */}
                <p className="text-lg font-extrabold leading-tight text-white">{school.name_en}</p>
                <p className="mt-0.5 text-xs text-brand-300">
                  {[school.short_name, school.address].filter(Boolean).join(' · ')}
                </p>
              </div>
            </div>

            <p className="font-bangla mt-4 max-w-sm text-sm leading-relaxed text-brand-200" lang="bn">
              {school.name_bn}
              <br />
              {school.grade_range_bn} · স্থাপিত {school.established}
            </p>

            <ul className="mt-6 space-y-2.5 text-sm">
              <li className="flex items-start gap-2.5">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-gold-400" aria-hidden="true" />
                <span>{school.address}</span>
              </li>
              <li className="flex items-center gap-2.5">
                <Phone className="h-4 w-4 shrink-0 text-gold-400" aria-hidden="true" />
                <a href={`tel:${(school.phone || '').replace(/\s/g, '')}`} className="hover:text-white">
                  {school.phone}
                </a>
              </li>
              <li className="flex items-center gap-2.5">
                <Mail className="h-4 w-4 shrink-0 text-gold-400" aria-hidden="true" />
                <a href={`mailto:${school.email}`} className="hover:text-white">
                  {school.email}
                </a>
              </li>
            </ul>
          </div>

          {/* Link columns */}
          {COLUMNS.map((column) => (
            <nav key={column.title} aria-label={column.title}>
              <h3 className="text-sm font-semibold text-white">{column.title}</h3>
              <ul className="mt-4 space-y-2.5 text-sm">
                {column.links.map((link) => (
                  <li key={link.label}>
                    {link.to ? (
                      <Link to={link.to} className="transition-colors hover:text-white">
                        {link.label}
                      </Link>
                    ) : (
                      <a href={link.href} className="transition-colors hover:text-white">
                        {link.label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center gap-3 border-t border-white/10 pt-6 text-xs text-brand-300 sm:flex-row sm:justify-between">
          <p>
            © {new Date().getFullYear()} {school.name_en}. All rights reserved.
          </p>

          <p className="text-center">
            Developed by <span className="font-semibold text-white">{DEVELOPER.name}</span>
            <a
              href={DEVELOPER.whatsapp}
              target="_blank"
              rel="noreferrer"
              className="ml-2 inline-flex items-center gap-1.5 align-middle transition-colors hover:text-white"
            >
              <MessageCircle className="h-3.5 w-3.5 shrink-0 text-gold-400" aria-hidden="true" />
              <span className="sr-only">WhatsApp </span>
              {DEVELOPER.phone}
            </a>
          </p>
        </div>
      </div>
    </footer>
  )
}

export default Footer
