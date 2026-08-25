import { Component } from 'react'
import { AlertOctagon } from 'lucide-react'

import Button from '@/components/ui/Button'

/**
 * Catches render-time crashes so a single broken screen does not leave the user
 * staring at a blank page.
 */
export class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error('Unhandled UI error:', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 px-4">
        <div className="max-w-md text-center">
          <span className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-crimson-50 text-crimson-600">
            <AlertOctagon className="h-8 w-8" aria-hidden="true" />
          </span>
          <h1 className="mt-6 text-2xl font-bold tracking-tight text-slate-900">Something went wrong</h1>
          <p className="mt-3 text-sm text-slate-600">
            The page ran into an unexpected error. Reloading usually clears it.
          </p>
          <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-100 p-3 text-left text-xs text-slate-600">
            {this.state.error.message}
          </pre>
          <Button className="mt-6" onClick={() => window.location.reload()}>
            Reload the page
          </Button>
        </div>
      </div>
    )
  }
}

export default ErrorBoundary
