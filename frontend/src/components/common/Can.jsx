import useAuth from '@/hooks/useAuth'

/**
 * Renders children only when the user holds the permission.
 *
 * This hides UI the user cannot use — it is *not* a security boundary. Django
 * re-checks every one of these codes on the API side, which is what actually
 * protects the data.
 */
export function Can({ permission, anyOf, allOf, fallback = null, children }) {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = useAuth()

  let allowed = true
  if (permission) allowed = hasPermission(permission)
  else if (anyOf?.length) allowed = hasAnyPermission(anyOf)
  else if (allOf?.length) allowed = hasAllPermissions(allOf)

  return allowed ? children : fallback
}

export default Can
