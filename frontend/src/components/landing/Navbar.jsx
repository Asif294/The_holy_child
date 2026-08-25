import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LayoutDashboard, Menu, ShieldCheck, X } from 'lucide-react'

import cn from '@/utils/cn'
import useAuth from '@/hooks/useAuth'
import useSchool from '@/hooks/useSchool'
import Button from '@/components/ui/Button'
import { Logo } from '@/components/common/Logo'

const LINKS = [
  { label: 'Home', href: '#home' },
  { label: 'About', href: '#about' },
  { label: 'Administration', href: '#administration' },
  { label: 'Teachers', href: '#teachers' },
  { label: 'Results', href: '#results' },
  { label: 'Contact', href: '#contact' },
]

/**
 * The public site's header.
 *
 * There is one action here, not two: **Admin**. Accounts are issued by the
 * school office rather than signed up for, so a "Get started" button would
 * lead nowhere. Once someone is signed in the same slot becomes their way back
 * into the dashboard.
 */
export function Navbar() {
  const { isAuthenticated, user } = useAuth()
  const { school } = useSchool()
  const [isOpen, setOpen] = useState(false)
  const [isScrolled, setScrolled] = useState(false)

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 8)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const action = isAuthenticated
    ? { to: '/app', label: 'Dashboard', icon: LayoutDashboard }
    : { to: '/login', label: 'Admin', icon: ShieldCheck }

  return (
    <header
      className={cn(
        'fixed inset-x-0 top-0 z-50 transition-all duration-200',
        isScrolled
          ? 'border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur-md'
          : 'border-b border-white/10 bg-brand-950/40 backdrop-blur-sm',
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="min-w-0" aria-label={`${school.name_en} home`}>
          <Logo variant={isScrolled ? 'dark' : 'light'} primary="school" />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className={cn(
                'rounded-lg px-3.5 py-2 text-sm font-medium transition-colors',
                isScrolled
                  ? 'text-slate-600 hover:bg-slate-100 hover:text-brand-700'
                  : 'text-brand-50 hover:bg-white/10 hover:text-white',
              )}
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          {isAuthenticated ? (
            <span className={cn('text-sm font-medium', isScrolled ? 'text-slate-500' : 'text-brand-100')}>
              {user?.full_name}
            </span>
          ) : null}
          <Link to={action.to}>
            <Button size="sm" leftIcon={<action.icon className="h-4 w-4" />}>
              {action.label}
            </Button>
          </Link>
        </div>

        <button
          type="button"
          onClick={() => setOpen((open) => !open)}
          className={cn(
            'rounded-lg p-2 transition-colors lg:hidden',
            isScrolled ? 'text-slate-600 hover:bg-slate-100' : 'text-white hover:bg-white/10',
          )}
          aria-label={isOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isOpen}
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      <div
        className={cn(
          'overflow-hidden border-t border-slate-200 bg-white transition-[max-height] duration-200 lg:hidden',
          isOpen ? 'max-h-[28rem]' : 'max-h-0 border-t-0',
        )}
      >
        <nav className="space-y-1 px-4 py-4" aria-label="Mobile">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              {link.label}
            </a>
          ))}
          <div className="pt-3">
            <Link to={action.to} onClick={() => setOpen(false)}>
              <Button className="w-full" leftIcon={<action.icon className="h-4 w-4" />}>
                {action.label}
              </Button>
            </Link>
          </div>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
