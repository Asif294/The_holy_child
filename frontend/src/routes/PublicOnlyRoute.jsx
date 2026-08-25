import { Navigate, Outlet } from 'react-router-dom'

import useAuth from '@/hooks/useAuth'
import { LoadingState } from '@/components/ui/Spinner'

/** Keeps an already-signed-in user off the login and register screens. */
export function PublicOnlyRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50">
        <LoadingState />
      </div>
    )
  }

  if (isAuthenticated) return <Navigate to="/app" replace />

  return children ?? <Outlet />
}

export default PublicOnlyRoute
