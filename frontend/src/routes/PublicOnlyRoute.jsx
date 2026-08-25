import { Navigate, Outlet } from 'react-router-dom'

import useAuth from '@/hooks/useAuth'
import { LoadingState } from '@/components/ui/Spinner'

/**
 * Keeps an already-signed-in user off the login screen.
 *
 * They land on the school's home page rather than the dashboard: the public
 * site is the front door for everyone, and the dashboard is one click on from
 * there for whoever has the permissions to use it.
 */
export function PublicOnlyRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <LoadingState />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/" replace />

  return children ?? <Outlet />
}

export default PublicOnlyRoute
