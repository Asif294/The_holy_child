import { useEffect, useState } from 'react'
import { Calendar, Info, Save, School, Upload } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { LoadingState } from '@/components/ui/Spinner'
import CrudPage from '@/components/common/CrudPage'
import { LogoMark } from '@/components/common/Logo'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useSchool from '@/hooks/useSchool'
import useToast from '@/hooks/useToast'
import { schoolService, sessionService } from '@/services'
import { formatDate } from '@/utils/formatters'
import { P } from '@/utils/permissions'

const TABS = [
  { id: 'school', label: 'School profile', icon: School },
  { id: 'sessions', label: 'Academic sessions', icon: Calendar },
]

/** The identity fields, laid out in the order they read on a letterhead. */
const PROFILE_FIELDS = [
  { name: 'name_en', label: 'Name (English)', required: true, fullWidth: true },
  { name: 'name_bn', label: 'Name (Bangla)', fullWidth: true },
  { name: 'short_name', label: 'Short name', hint: 'Used in the sidebar and on narrow screens.' },
  { name: 'brand_name', label: 'Brand wordmark', hint: 'Shown beside the crest.' },
  { name: 'village', label: 'Village / area' },
  { name: 'upazila', label: 'Upazila' },
  { name: 'district', label: 'District' },
  { name: 'country', label: 'Country' },
  { name: 'established', label: 'Established' },
  { name: 'phone', label: 'Phone', type: 'tel' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'website', label: 'Website', type: 'url', placeholder: 'https://…' },
  { name: 'grade_range', label: 'Grades offered' },
  { name: 'grade_range_bn', label: 'Grades offered (Bangla)' },
]

const MAX_LOGO_BYTES = 2 * 1024 * 1024

function SchoolProfileTab() {
  const toast = useToast()
  const { hasPermission } = useAuth()
  const { school, refresh } = useSchool()
  const canEdit = hasPermission(P.setting.update)

  const { data, isLoading, error } = useApi(() => schoolService.profile(), [])
  const [values, setValues] = useState(null)
  const [logoFile, setLogoFile] = useState(null)
  const [logoPreview, setLogoPreview] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [isSaving, setIsSaving] = useState(false)

  // Seed the form once the profile lands.
  useEffect(() => {
    if (data) setValues(Object.fromEntries(PROFILE_FIELDS.map((f) => [f.name, data[f.name] ?? ''])))
  }, [data])

  // A preview URL is a live object handle; revoke it so it cannot leak.
  useEffect(() => {
    if (!logoFile) return undefined
    const url = URL.createObjectURL(logoFile)
    setLogoPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [logoFile])

  if (isLoading || !values) return <LoadingState />
  if (error) {
    return (
      <Alert type="error" title="Could not load the school profile">
        {error.message}
      </Alert>
    )
  }

  const setField = (name, value) => {
    setValues((current) => ({ ...current, [name]: value }))
    setFieldErrors((current) => (current[name] ? { ...current, [name]: undefined } : current))
  }

  const onPickLogo = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Choose an image file for the logo.')
      return
    }
    if (file.size > MAX_LOGO_BYTES) {
      toast.error('The logo must be 2 MB or smaller.')
      return
    }
    setLogoFile(file)
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    setIsSaving(true)
    setFieldErrors({})
    try {
      await schoolService.updateProfile(values, logoFile)
      setLogoFile(null)
      await refresh()
      toast.success('School profile saved.')
    } catch (caught) {
      setFieldErrors(caught.errors ?? {})
      toast.error(caught.message ?? 'Could not save the school profile.')
    } finally {
      setIsSaving(false)
    }
  }

  const currentLogo = logoPreview || school.logo_url

  return (
    <form onSubmit={onSubmit} className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader
          title="School profile"
          description="Shown across the admin, the login screen and the public site."
        />
        <CardBody>
          {!canEdit ? (
            <Alert type="info" className="mb-5">
              You can view these details but not change them. The{' '}
              <span className="font-mono text-xs">setting.update</span> permission is required to edit.
            </Alert>
          ) : null}

          {/* Crest */}
          <div className="mb-6 flex flex-wrap items-center gap-4 rounded-lg border border-slate-200 bg-slate-50/60 p-4">
            <span className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-white">
              {currentLogo ? (
                <img src={currentLogo} alt="School logo" className="h-full w-full object-contain" />
              ) : (
                <LogoMark className="h-12 w-12" />
              )}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-slate-900">School logo</p>
              <p className="mt-0.5 text-xs text-slate-500">
                Square PNG or SVG works best, up to 2&nbsp;MB. Without one, the built-in crest is used.
              </p>
              {logoFile ? (
                <p className="mt-1 text-xs font-medium text-brand-700">
                  {logoFile.name} — not saved yet
                </p>
              ) : null}
            </div>
            {canEdit ? (
              <label className="shrink-0 cursor-pointer">
                <span className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  Choose file
                </span>
                <input type="file" accept="image/*" className="sr-only" onChange={onPickLogo} />
              </label>
            ) : null}
          </div>

          {/* Identity fields */}
          <div className="grid gap-4 sm:grid-cols-2">
            {PROFILE_FIELDS.map((field) => (
              <Input
                key={field.name}
                label={field.label}
                type={field.type ?? 'text'}
                value={values[field.name]}
                onChange={(event) => setField(field.name, event.target.value)}
                required={field.required}
                disabled={!canEdit}
                placeholder={field.placeholder}
                hint={field.hint}
                error={fieldErrors[field.name]?.[0]}
                containerClassName={field.fullWidth ? 'sm:col-span-2' : undefined}
              />
            ))}
          </div>

          <p className="mt-4 text-xs text-slate-500">
            Address shown publicly:{' '}
            <span className="font-medium text-slate-700">
              {[values.village, values.upazila, values.district, values.country].filter(Boolean).join(', ') || '—'}
            </span>
          </p>

          {canEdit ? (
            <div className="mt-6 flex justify-end gap-2 border-t border-slate-100 pt-4">
              <Button
                type="button"
                variant="secondary"
                disabled={isSaving}
                onClick={() => {
                  setValues(Object.fromEntries(PROFILE_FIELDS.map((f) => [f.name, data[f.name] ?? ''])))
                  setLogoFile(null)
                  setFieldErrors({})
                }}
              >
                Reset
              </Button>
              <Button type="submit" isLoading={isSaving} leftIcon={<Save className="h-4 w-4" />}>
                Save changes
              </Button>
            </div>
          ) : null}
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Headline counts" action={<Info className="h-4 w-4 text-slate-400" aria-hidden="true" />} />
        <CardBody>
          <dl className="space-y-3.5 text-sm">
            {Object.entries(school.stats ?? {}).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between border-b border-slate-100 pb-2.5">
                <dt className="capitalize text-slate-500">{key}</dt>
                <dd className="font-semibold text-slate-900">{value}</dd>
              </div>
            ))}
          </dl>
          <Alert type="info" className="mt-5">
            These figures are live counts from the database and are not editable.
          </Alert>
        </CardBody>
      </Card>
    </form>
  )
}

function SessionsTab() {
  return (
    <CrudPage
      title="Academic sessions"
      description="School years. Exactly one session is current at a time."
      service={sessionService}
      module="class"
      singular="session"
      searchPlaceholder="Search sessions…"
      columns={[
        { key: 'name', header: 'Session', render: (row) => <span className="font-medium text-slate-900">{row.name}</span> },
        { key: 'start_date', header: 'Starts', render: (row) => formatDate(row.start_date) },
        { key: 'end_date', header: 'Ends', render: (row) => formatDate(row.end_date) },
        {
          key: 'is_current',
          header: 'Current',
          render: (row) => (row.is_current ? <Badge tone="success">Current</Badge> : <Badge tone="neutral">Past</Badge>),
        },
      ]}
      fields={[
        { name: 'name', label: 'Session name', required: true, placeholder: '2026' },
        { name: 'start_date', label: 'Start date', type: 'date', required: true },
        { name: 'end_date', label: 'End date', type: 'date', required: true },
        { name: 'is_current', label: 'Mark as the current session', type: 'checkbox', fullWidth: true },
      ]}
      toPayload={(payload, values) => ({ ...payload, is_current: Boolean(values.is_current) })}
    />
  )
}

export function Settings() {
  useDocumentTitle('Settings')
  const [tab, setTab] = useState('school')

  return (
    <div>
      <PageHeader title="Settings" description="School identity and academic calendar configuration." />

      <div className="mb-6 flex gap-1 border-b border-slate-200">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            onClick={() => setTab(entry.id)}
            className={`-mb-px flex items-center gap-2 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors ${
              tab === entry.id
                ? 'border-brand-600 text-brand-700'
                : 'border-transparent text-slate-500 hover:border-slate-300 hover:text-slate-700'
            }`}
          >
            <entry.icon className="h-4 w-4" aria-hidden="true" />
            {entry.label}
          </button>
        ))}
      </div>

      {tab === 'school' ? <SchoolProfileTab /> : <SessionsTab />}
    </div>
  )
}

export default Settings
