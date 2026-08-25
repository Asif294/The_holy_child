import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bell, ChevronDown, LogOut, Menu, Search, Settings, User } from 'lucide-react'

import cn from '@/utils/cn'
import useAuth from '@/hooks/useAuth'
import useClickOutside from '@/hooks/useClickOutside'
import useToast from '@/hooks/useToast'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'

export function Topbar({ onOpenMobileNav, notices = [] }) {
  const { user, logout } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [isProfileOpen, setProfileOpen] = useState(false)
  const [isBellOpen, setBellOpen] = useState(false)
  const profileRef = useRef(null)
  const bellRef = useRef(null)

  useClickOutside(profileRef, () => setProfileOpen(false), isProfileOpen)
  useClickOutside(bellRef, () => setBellOpen(false), isBellOpen)

  async function handleLogout() {
    setProfileOpen(false)
    await logout()
    toast.success('You have been signed out.')
    navigate('/login', { replace: true })
  }

  const roleName = user?.role?.name ?? user?.role ?? 'No role'

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur-md sm:px-6">
      <button
        type="button"
        onClick={onOpenMobileNav}
        className="-ml-1 rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 lg:hidden"
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Search */}
      <form
        className="relative hidden max-w-md flex-1 sm:block"
        onSubmit={(event) => {
          event.preventDefault()
          const query = new FormData(event.currentTarget).get('q')?.toString().trim()
          if (query) navigate(`/app/students?search=${encodeURIComponent(query)}`)
        }}
        role="search"
      >
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="search"
          name="q"
          placeholder="Search students, teachers…"
          aria-label="Search"
          className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 transition-colors focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/15"
        />
      </form>

      <div className="ml-auto flex items-center gap-1.5">
        {/* Notifications */}
        <div className="relative" ref={bellRef}>
          <button
            type="button"
            onClick={() => setBellOpen((open) => !open)}
            className="relative rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
            aria-label={`Notifications${notices.length ? `, ${notices.length} unread` : ''}`}
            aria-expanded={isBellOpen}
          >
            <Bell className="h-5 w-5" />
            {notices.length ? (
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full rounded-full bg-crimson-500 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-crimson-600" />
              </span>
            ) : null}
          </button>

          {isBellOpen ? (
            <div className="absolute right-0 top-full mt-2 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[var(--shadow-float)]">
              <div className="border-b border-slate-100 px-4 py-3">
                <p className="text-sm font-semibold text-slate-900">Notices</p>
              </div>
              <ul className="max-h-80 divide-y divide-slate-100 overflow-y-auto">
                {notices.length === 0 ? (
                  <li className="px-4 py-8 text-center text-sm text-slate-500">No notices right now.</li>
                ) : (
                  notices.slice(0, 5).map((notice) => (
                    <li key={notice.id} className="px-4 py-3 transition-colors hover:bg-slate-50">
                      <p className="text-sm font-medium text-slate-800">{notice.title}</p>
                      <p className="mt-0.5 line-clamp-2 text-xs text-slate-500">{notice.body}</p>
                    </li>
                  ))
                )}
              </ul>
              <Link
                to="/app/notices"
                onClick={() => setBellOpen(false)}
                className="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-brand-600 hover:bg-slate-50"
              >
                View all notices
              </Link>
            </div>
          ) : null}
        </div>

        {/* Profile */}
        <div className="relative" ref={profileRef}>
          <button
            type="button"
            onClick={() => setProfileOpen((open) => !open)}
            className="flex items-center gap-2.5 rounded-lg py-1.5 pl-1.5 pr-2 transition-colors hover:bg-slate-100"
            aria-expanded={isProfileOpen}
            aria-haspopup="menu"
          >
            <Avatar src={user?.profile_image_url} name={user?.full_name ?? user?.name} size="sm" />
            <span className="hidden text-left leading-tight sm:block">
              <span className="block max-w-[10rem] truncate text-sm font-semibold text-slate-800">
                {user?.full_name ?? user?.name}
              </span>
              <span className="block text-xs text-slate-500">{roleName}</span>
            </span>
            <ChevronDown className={cn('h-4 w-4 text-slate-400 transition-transform', isProfileOpen && 'rotate-180')} />
          </button>

          {isProfileOpen ? (
            <div
              role="menu"
              className="absolute right-0 top-full mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-[var(--shadow-float)]"
            >
              <div className="border-b border-slate-100 px-4 py-3.5">
                <p className="truncate text-sm font-semibold text-slate-900">{user?.full_name ?? user?.name}</p>
                <p className="truncate text-xs text-slate-500">{user?.email}</p>
                <Badge tone="brand" className="mt-2">
                  {roleName}
                </Badge>
              </div>
              <div className="p-1.5">
                <Link
                  to="/app/profile"
                  role="menuitem"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                >
                  <User className="h-4 w-4 text-slate-400" /> My Profile
                </Link>
                <Link
                  to="/app/settings"
                  role="menuitem"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100"
                >
                  <Settings className="h-4 w-4 text-slate-400" /> Settings
                </Link>
              </div>
              <div className="border-t border-slate-100 p-1.5">
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium text-crimson-600 transition-colors hover:bg-crimson-50"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </header>
  )
}

export default Topbar
