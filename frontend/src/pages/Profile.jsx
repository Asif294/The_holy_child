import { useEffect, useState } from 'react'
import { KeyRound, Save, ShieldCheck, User } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import Input, { Select } from '@/components/ui/Input'
import PageHeader from '@/components/common/PageHeader'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'
import authService from '@/services/authService'
import { formatDateTime } from '@/utils/formatters'

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
]

export function Profile() {
  useDocumentTitle('My profile')

  const { user, refreshUser } = useAuth()
  const toast = useToast()

  const [profile, setProfile] = useState({ full_name: '', phone: '', gender: '', date_of_birth: '', address: '' })
  const [profileErrors, setProfileErrors] = useState({})
  const [isSavingProfile, setSavingProfile] = useState(false)

  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    new_password_confirmation: '',
  })
  const [passwordErrors, setPasswordErrors] = useState({})
  const [isSavingPassword, setSavingPassword] = useState(false)

  useEffect(() => {
    if (!user) return
    setProfile({
      full_name: user.full_name ?? '',
      phone: user.phone ?? '',
      gender: user.gender ?? '',
      date_of_birth: user.date_of_birth ?? '',
      address: user.address ?? '',
    })
  }, [user])

  async function saveProfile(event) {
    event.preventDefault()
    setSavingProfile(true)
    setProfileErrors({})
    try {
      const payload = Object.fromEntries(Object.entries(profile).filter(([, value]) => value !== ''))
      await authService.updateProfile(payload)
      await refreshUser()
      toast.success('Profile updated.')
    } catch (error) {
      setProfileErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSavingProfile(false)
    }
  }

  async function savePassword(event) {
    event.preventDefault()
    setSavingPassword(true)
    setPasswordErrors({})
    try {
      await authService.changePassword(passwords)
      setPasswords({ current_password: '', new_password: '', new_password_confirmation: '' })
      toast.success('Password changed.')
    } catch (error) {
      setPasswordErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSavingPassword(false)
    }
  }

  function errorFor(errors, field) {
    const value = errors[field]
    return Array.isArray(value) ? value[0] : value
  }

  return (
    <div>
      <PageHeader title="My profile" description="Your account details and the permissions your role carries." />

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Identity */}
        <Card>
          <CardBody className="text-center">
            <Avatar src={user?.profile_image_url} name={user?.full_name} size="xl" className="mx-auto" />
            <p className="mt-4 text-lg font-semibold text-slate-900">{user?.full_name}</p>
            <p className="text-sm text-slate-500">{user?.email}</p>
            <Badge tone="brand" className="mt-3">
              {user?.role?.name ?? 'No role'}
            </Badge>

            <dl className="mt-6 space-y-3 border-t border-slate-100 pt-5 text-left text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Username</dt>
                <dd className="font-medium text-slate-800">{user?.username}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Last sign-in</dt>
                <dd className="font-medium text-slate-800">{formatDateTime(user?.last_login)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Permissions</dt>
                <dd className="font-medium text-slate-800">{user?.permissions?.length ?? 0}</dd>
              </div>
            </dl>
          </CardBody>
        </Card>

        {/* Editable details */}
        <Card className="lg:col-span-2">
          <CardHeader
            title="Account details"
            description="You can update your own details here — your role can only be changed by an administrator."
            action={<User className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <CardBody>
            <form onSubmit={saveProfile} className="grid gap-4 sm:grid-cols-2" noValidate>
              <Input
                label="Full name"
                required
                value={profile.full_name}
                onChange={(event) => setProfile((c) => ({ ...c, full_name: event.target.value }))}
                error={errorFor(profileErrors, 'full_name')}
              />
              <Input label="Email address" value={user?.email ?? ''} disabled hint="Contact an administrator to change this." />
              <Input
                label="Phone"
                type="tel"
                value={profile.phone}
                onChange={(event) => setProfile((c) => ({ ...c, phone: event.target.value }))}
                error={errorFor(profileErrors, 'phone')}
              />
              <Select
                label="Gender"
                placeholder="Not specified"
                options={GENDER_OPTIONS}
                value={profile.gender}
                onChange={(event) => setProfile((c) => ({ ...c, gender: event.target.value }))}
              />
              <Input
                label="Date of birth"
                type="date"
                value={profile.date_of_birth}
                onChange={(event) => setProfile((c) => ({ ...c, date_of_birth: event.target.value }))}
              />
              <Input
                label="Address"
                value={profile.address}
                onChange={(event) => setProfile((c) => ({ ...c, address: event.target.value }))}
              />
              <div className="sm:col-span-2">
                <Button type="submit" leftIcon={<Save className="h-4 w-4" />} isLoading={isSavingProfile}>
                  Save changes
                </Button>
              </div>
            </form>
          </CardBody>
        </Card>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {/* Password */}
        <Card>
          <CardHeader
            title="Change password"
            description="Passwords are validated against Django's password policy."
            action={<KeyRound className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <CardBody>
            <form onSubmit={savePassword} className="space-y-4" noValidate>
              <Input
                label="Current password"
                type="password"
                autoComplete="current-password"
                required
                value={passwords.current_password}
                onChange={(event) => setPasswords((c) => ({ ...c, current_password: event.target.value }))}
                error={errorFor(passwordErrors, 'current_password')}
              />
              <Input
                label="New password"
                type="password"
                autoComplete="new-password"
                required
                value={passwords.new_password}
                onChange={(event) => setPasswords((c) => ({ ...c, new_password: event.target.value }))}
                error={errorFor(passwordErrors, 'new_password')}
              />
              <Input
                label="Confirm new password"
                type="password"
                autoComplete="new-password"
                required
                value={passwords.new_password_confirmation}
                onChange={(event) =>
                  setPasswords((c) => ({ ...c, new_password_confirmation: event.target.value }))
                }
                error={errorFor(passwordErrors, 'new_password_confirmation')}
              />
              <Button type="submit" isLoading={isSavingPassword}>
                Change password
              </Button>
            </form>
          </CardBody>
        </Card>

        {/* Permissions */}
        <Card>
          <CardHeader
            title="Your permissions"
            description={`Inherited from the ${user?.role?.name ?? 'assigned'} role.`}
            action={<ShieldCheck className="h-4 w-4 text-slate-400" aria-hidden="true" />}
          />
          <CardBody>
            {user?.is_superuser ? (
              <Alert type="info">
                You are a superuser — every permission check passes for your account.
              </Alert>
            ) : null}

            {user?.permissions?.length ? (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {user.permissions.map((code) => (
                  <span
                    key={code}
                    className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700 ring-1 ring-inset ring-slate-200"
                  >
                    {code}
                  </span>
                ))}
              </div>
            ) : (
              <Alert type="warning">
                Your account holds no permissions yet. Ask an administrator to assign you a role.
              </Alert>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

export default Profile
