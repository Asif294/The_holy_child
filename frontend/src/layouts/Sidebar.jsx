import { Link, NavLink } from 'react-router-dom'
import { ChevronLeft, X } from 'lucide-react'

import cn from '@/utils/cn'
import useAuth from '@/hooks/useAuth'
import { Logo, LogoMark } from '@/components/common/Logo'
import { visibleNavigation } from '@/utils/navigation'

export function Sidebar({ isCollapsed, onToggleCollapse, isMobileOpen, onCloseMobile }) {
  const { hasPermission, hasAnyPermission } = useAuth()
  const sections = visibleNavigation({ hasPermission, hasAnyPermission })

  return (
    <>
      {/* Mobile scrim */}
      <div
        className={cn(
          'fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-[1px] transition-opacity lg:hidden',
          isMobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onCloseMobile}
        aria-hidden="true"
      />

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 flex flex-col border-r border-brand-800/40 bg-brand-900 transition-[width,transform] duration-200',
          isCollapsed ? 'w-[72px]' : 'w-64',
          isMobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
        aria-label="Main navigation"
      >
        {/* Brand — the school's own name and crest, so it leads to the school's
            public home page rather than back to the dashboard. */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-4">
          <Link
            to="/"
            onClick={onCloseMobile}
            title="Go to the school website"
            aria-label="Go to the school website"
            className={cn(
              'min-w-0 rounded-lg transition-opacity hover:opacity-80',
              isCollapsed && 'mx-auto',
            )}
          >
            {isCollapsed ? (
              <LogoMark className="h-9 w-9" />
            ) : (
              <Logo variant="light" markClassName="h-9 w-9" />
            )}
          </Link>
          <button
            type="button"
            onClick={onCloseMobile}
            className="rounded-lg p-1.5 text-brand-200 hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Menu */}
        <nav className="scrollbar-slim flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {sections.map((section) => (
            <div key={section.id}>
              {section.title && !isCollapsed ? (
                <p className="mb-1.5 px-3 text-[11px] font-semibold uppercase tracking-wider text-brand-300/80">
                  {section.title}
                </p>
              ) : null}
              {section.title && isCollapsed ? <div className="mx-3 mb-2 border-t border-white/10" /> : null}

              <ul className="space-y-0.5">
                {section.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.end}
                      onClick={onCloseMobile}
                      title={isCollapsed ? item.label : undefined}
                      className={({ isActive }) =>
                        cn(
                          'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                          isCollapsed && 'justify-center px-0',
                          isActive
                            ? 'bg-white text-brand-800 shadow-sm'
                            : 'text-brand-100 hover:bg-white/10 hover:text-white',
                        )
                      }
                    >
                      <item.icon className="h-[18px] w-[18px] shrink-0" aria-hidden="true" />
                      {!isCollapsed ? <span className="truncate">{item.label}</span> : null}
                      {isCollapsed ? <span className="sr-only">{item.label}</span> : null}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {sections.length === 0 ? (
            <p className="px-3 py-6 text-sm text-brand-200">
              Your role does not grant access to any module yet. Please contact an administrator.
            </p>
          ) : null}
        </nav>

        {/* Collapse toggle — desktop only */}
        <div className="hidden shrink-0 border-t border-white/10 p-3 lg:block">
          <button
            type="button"
            onClick={onToggleCollapse}
            className={cn(
              'flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-brand-100 transition-colors hover:bg-white/10 hover:text-white',
              isCollapsed && 'justify-center px-0',
            )}
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft className={cn('h-4 w-4 transition-transform', isCollapsed && 'rotate-180')} />
            {!isCollapsed ? <span>Collapse</span> : null}
          </button>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
