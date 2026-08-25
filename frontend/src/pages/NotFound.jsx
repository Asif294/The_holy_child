import { Link } from 'react-router-dom'
import { Compass } from 'lucide-react'

import Button from '@/components/ui/Button'
import useDocumentTitle from '@/hooks/useDocumentTitle'

export function NotFound() {
  useDocumentTitle('404 · Not found')

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50 px-4">
      <div className="max-w-md text-center">
        <span className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-50 text-brand-600">
          <Compass className="h-8 w-8" aria-hidden="true" />
        </span>
        <p className="mt-6 text-sm font-semibold uppercase tracking-wider text-brand-600">404</p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Page not found</h1>
        <p className="mt-3 text-sm text-slate-600">
          The page you are looking for has moved or never existed.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/">
            <Button variant="secondary">Go to home</Button>
          </Link>
          <Link to="/app">
            <Button>Open dashboard</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default NotFound
