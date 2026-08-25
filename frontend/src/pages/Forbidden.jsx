import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, ShieldAlert } from 'lucide-react'

import Button from '@/components/ui/Button'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'

export function Forbidden() {
  useDocumentTitle('403 · Forbidden')

  const navigate = useNavigate()
  const { user } = useAuth()
  const roleName = user?.role?.name ?? user?.role

  return (
    <div className="grid min-h-[70vh] place-items-center px-4">
      <div className="max-w-md text-center">
        <span className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-crimson-50 text-crimson-600">
          <ShieldAlert className="h-8 w-8" aria-hidden="true" />
        </span>

        <p className="mt-6 text-sm font-semibold uppercase tracking-wider text-crimson-600">403 Forbidden</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
          You don&rsquo;t have access to this page
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-600">
          {roleName ? (
            <>
              Your role <span className="font-semibold text-slate-800">{roleName}</span> does not carry the
              permission this screen requires. Ask an administrator to grant it, or head back to your dashboard.
            </>
          ) : (
            'Your account does not carry the permission this screen requires.'
          )}
        </p>

        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Button variant="secondary" leftIcon={<ArrowLeft className="h-4 w-4" />} onClick={() => navigate(-1)}>
            Go back
          </Button>
          <Link to="/app">
            <Button>Back to dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Forbidden
