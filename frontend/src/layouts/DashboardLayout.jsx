import { useCallback, useEffect, useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

import cn from '@/utils/cn'
import useAuth from '@/hooks/useAuth'
import { noticeService } from '@/services'
import { STORAGE_KEYS } from '@/utils/constants'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export function DashboardLayout() {
  const { hasPermission } = useAuth()
  const location = useLocation()

  const [isCollapsed, setCollapsed] = useState(
    () => localStorage.getItem(STORAGE_KEYS.sidebarCollapsed) === 'true',
  )
  const [isMobileOpen, setMobileOpen] = useState(false)
  const [notices, setNotices] = useState([])

  const toggleCollapse = useCallback(() => {
    setCollapsed((collapsed) => {
      localStorage.setItem(STORAGE_KEYS.sidebarCollapsed, String(!collapsed))
      return !collapsed
    })
  }, [])

  // Close the mobile drawer whenever the route changes.
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  useEffect(() => {
    if (!hasPermission('notice.view')) return
    noticeService
      .list({ is_published: true, page_size: 5 })
      .then((data) => setNotices(data.results ?? []))
      .catch(() => setNotices([]))
  }, [hasPermission])

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={toggleCollapse}
        isMobileOpen={isMobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      <div className={cn('flex min-h-screen flex-col transition-[padding] duration-200', isCollapsed ? 'lg:pl-[72px]' : 'lg:pl-64')}>
        <Topbar onOpenMobileNav={() => setMobileOpen(true)} notices={notices} />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default DashboardLayout
