import { Navigate, Outlet } from 'react-router-dom'

import useAuth from '@/hooks/useAuth'
import { LoadingState } from '@/components/ui/Spinner'

/**
 * Requires a specific permission code on top of authentication.
 *
 * This is a *navigation* guard — it stops a user from landing on a screen whose
 * data they cannot load. The API enforces the same code independently, so
 * bypassing this guard in the browser gains nothing.
 */
export function PermissionRoute({ permission, anyOf, allOf, children, redirectTo = '/403' }) {
  const { isAuthenticated, isLoading, hasPermission, hasAnyPermission, hasAllPermissions } = useAuth()

  if (isLoading) {
    return (
      <div className="grid min-h-[50vh] place-items-center">
        <LoadingState label="Checking your access…" />
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />

  let allowed = true
  if (permission) allowed = hasPermission(permission)
  else if (anyOf?.length) allowed = hasAnyPermission(anyOf)
  else if (allOf?.length) allowed = hasAllPermissions(allOf)

  if (!allowed) return <Navigate to={redirectTo} replace />

  return children ?? <Outlet />
}

export default PermissionRoute
