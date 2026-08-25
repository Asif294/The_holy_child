import { Navigate, Outlet, useLocation } from 'react-router-dom'

import useAuth from '@/hooks/useAuth'
import { LoadingState } from '@/components/ui/Spinner'

/**
 * Requires an authenticated session.
 *
 * Wraps either an `<Outlet />` (route-level) or explicit children. While the
 * stored token is being validated we hold the screen rather than bouncing the
 * user to the login page and back.
 */
export function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <LoadingState label="Checking your session…" />
      </div>
    )
  }

  if (!isAuthenticated) {
    // Remember where they were headed so login can send them back.
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children ?? <Outlet />
}

export default ProtectedRoute
