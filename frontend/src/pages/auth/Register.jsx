import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Lock, Mail, Phone, User } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'

const INITIAL = {
  full_name: '',
  email: '',
  phone: '',
  password: '',
  password_confirmation: '',
}

/** Mirrors Django's validators closely enough to catch mistakes before a round trip. */
function passwordStrength(password) {
  let score = 0
  if (password.length >= 8) score += 1
  if (password.length >= 12) score += 1
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1
  return Math.min(score, 4)
}

const STRENGTH = [
  { label: 'Too weak', bar: 'w-1/4 bg-crimson-500', text: 'text-crimson-600' },
  { label: 'Weak', bar: 'w-2/4 bg-gold-500', text: 'text-gold-700' },
  { label: 'Good', bar: 'w-3/4 bg-sky-500', text: 'text-sky-600' },
  { label: 'Strong', bar: 'w-full bg-emerald-500', text: 'text-emerald-600' },
]

export function Register() {
  useDocumentTitle('Create an account')

  const { register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState(INITIAL)
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState(null)
  const [isSubmitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
    setErrors((current) => ({ ...current, [field]: undefined }))
  }

  function validate() {
    const next = {}
    if (form.full_name.trim().length < 3) next.full_name = 'Enter your full name (at least 3 characters).'
    if (!/^\S+@\S+\.\S+$/.test(form.email.trim())) next.email = 'Enter a valid email address.'
    const digits = form.phone.replace(/[\s+-]/g, '')
    if (!/^\d{6,15}$/.test(digits)) next.phone = 'Enter a valid phone number.'
    if (form.password.length < 8) next.password = 'Use at least 8 characters.'
    if (form.password !== form.password_confirmation) {
      next.password_confirmation = 'The two passwords do not match.'
    }
    return next
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setFormError(null)

    const nextErrors = validate()
    if (Object.keys(nextErrors).length) {
      setErrors(nextErrors)
      return
    }

    setSubmitting(true)
    try {
      const user = await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
        password_confirmation: form.password_confirmation,
      })
      toast.success(`Account created. Welcome, ${user.full_name ?? user.name}.`)
      navigate('/app', { replace: true })
    } catch (error) {
      setErrors(error.errors ?? {})
      setFormError(error.message)
    } finally {
      setSubmitting(false)
    }
  }

  const strength = form.password ? STRENGTH[Math.max(passwordStrength(form.password) - 1, 0)] : null

  function errorFor(field) {
    const value = errors[field]
    return Array.isArray(value) ? value[0] : value
  }

  return (
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">Create your account</h1>
      <p className="mt-1.5 text-sm text-slate-500">
        New accounts start with the default role. An administrator assigns staff roles afterwards.
      </p>

      {formError ? (
        <Alert type="error" className="mt-5">
          {formError}
        </Alert>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
        <Input
          label="Full name"
          name="full_name"
          autoComplete="name"
          placeholder="Rahim Uddin"
          leftIcon={<User className="h-4 w-4" />}
          value={form.full_name}
          onChange={(event) => update('full_name', event.target.value)}
          error={errorFor('full_name')}
          required
        />

        <Input
          label="Email address"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="you@example.com"
          leftIcon={<Mail className="h-4 w-4" />}
          value={form.email}
          onChange={(event) => update('email', event.target.value)}
          error={errorFor('email')}
          required
        />

        <Input
          label="Phone number"
          type="tel"
          name="phone"
          autoComplete="tel"
          placeholder="+8801700000000"
          leftIcon={<Phone className="h-4 w-4" />}
          value={form.phone}
          onChange={(event) => update('phone', event.target.value)}
          error={errorFor('phone')}
          required
        />

        <div>
          <Input
            label="Password"
            type={showPassword ? 'text' : 'password'}
            name="password"
            autoComplete="new-password"
            placeholder="At least 8 characters"
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
          {strength ? (
            <div className="mt-2 flex items-center gap-2.5">
              <div className="h-1 flex-1 overflow-hidden rounded-full bg-slate-200">
                <div className={`h-full rounded-full transition-all ${strength.bar}`} />
              </div>
              <span className={`text-xs font-medium ${strength.text}`}>{strength.label}</span>
            </div>
          ) : null}
        </div>

        <Input
          label="Confirm password"
          type={showPassword ? 'text' : 'password'}
          name="password_confirmation"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          leftIcon={<Lock className="h-4 w-4" />}
          value={form.password_confirmation}
          onChange={(event) => update('password_confirmation', event.target.value)}
          error={errorFor('password_confirmation')}
          required
        />

        <Button type="submit" size="lg" className="w-full" isLoading={isSubmitting}>
          Create account
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-500">
        Already have an account?{' '}
        <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-700">
          Sign in
        </Link>
      </p>
    </div>
  )
}

export default Register
