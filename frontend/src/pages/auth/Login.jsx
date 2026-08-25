import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, Eye, EyeOff, Lock, UserRound } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'

/**
 * The only way into the system.
 *
 * There is no self-registration: accounts are created by an administrator, who
 * also decides the role each one carries. Signing in lands on the school's own
 * home page — the dashboard is one click further, behind whichever permissions
 * the account holds.
 */
export function Login() {
  useDocumentTitle('Sign in')

  const { login, sessionExpired, dismissSessionExpiry } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ identifier: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [isSubmitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError(null)
    dismissSessionExpiry()

    const nextErrors = {}
    if (!form.identifier.trim()) nextErrors.identifier = 'Enter your email address or phone number.'
    if (!form.password) nextErrors.password = 'Enter your password.'
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      return
    }

    setSubmitting(true)
    try {
      const user = await login({ identifier: form.identifier.trim(), password: form.password })
      toast.success(`Welcome back, ${user.full_name ?? user.name}.`)
      // Back to wherever they were headed, or to the school's home page.
      navigate(location.state?.from?.pathname ?? '/', { replace: true })
    } catch (error) {
      setErrors(error.errors ?? {})
      setFormError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  function errorFor(field) {
    const value = errors[field]
    return Array.isArray(value) ? value[0] : value
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">Sign in</h1>
      <p className="mt-1.5 text-sm text-slate-500">
        For staff and students of the school. Use the email address or mobile number the office has on file.
      </p>

      {sessionExpired ? (
        <Alert type="warning" className="mt-5">
          Your session expired. Please sign in again.
        </Alert>
      ) : null}

      {formError ? (
        <Alert type="error" className="mt-5">
          {formError}
        </Alert>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
        <Input
          label="Email address or phone number"
          type="text"
          name="identifier"
          autoComplete="username"
          placeholder="you@holychildschool.edu.bd or 01700000000"
          leftIcon={<UserRound className="h-4 w-4" />}
          value={form.identifier}
          onChange={(event) => update('identifier', event.target.value)}
          error={errorFor('identifier')}
          required
        />

        <Input
          label="Password"
          type={showPassword ? 'text' : 'password'}
          name="password"
          autoComplete="current-password"
          placeholder="••••••••"
          leftIcon={<Lock className="h-4 w-4" />}
          value={form.password}
          onChange={(event) => update('password', event.target.value)}
          error={errorFor('password')}
          required
          rightSlot={
            <button
              type="button"
              onClick={() => setShowPassword((shown) => !shown)}
              className="text-slate-400 transition-colors hover:text-slate-600"
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          }
        />

        <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>
          Sign in
        </Button>
      </form>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3.5">
        <p className="text-sm text-slate-600">
          Accounts are issued by the school office — there is no public sign-up. If you have lost your
          password, ask an administrator to reset it; you can change it yourself from your profile once
          you are signed in.
        </p>
      </div>

      <p className="mt-6 text-center text-sm">
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 font-medium text-slate-500 transition-colors hover:text-brand-600"
        >
          <ArrowLeft className="h-4 w-4" /> Back to the school website
        </Link>
      </p>
    </div>
  )
}

export default Login
