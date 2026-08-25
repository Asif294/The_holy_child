import { useState } from 'react'
import { BadgeCheck, ClipboardCheck, ExternalLink, FileWarning, GraduationCap, Pencil, Users } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Avatar from '@/components/ui/Avatar'
import Badge, { StatusBadge } from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Card, { CardBody, CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Modal from '@/components/ui/Modal'
import { LoadingState } from '@/components/ui/Spinner'
import Can from '@/components/common/Can'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import StatCard from '@/components/dashboard/StatCard'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import useToast from '@/hooks/useToast'
import { principalService } from '@/services'
import { formatDate, formatNumber, humanise } from '@/utils/formatters'

/** The two seats the public Administration section renders. */
const OFFICES = [
  { key: 'principal', label: 'Principal', description: "The head of the institution." },
  { key: 'vice_principal', label: 'Vice Principal', description: 'Second in the administration.' },
]

const FIELDS = [
  { name: 'full_name', label: 'Full name', required: true },
  { name: 'designation', label: 'Designation', placeholder: 'Principal' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'phone', label: 'Phone', type: 'tel' },
  { name: 'qualification', label: 'Qualification', placeholder: 'M.A. in English, B.Ed.' },
  { name: 'experience_years', label: 'Years of experience', type: 'number', min: 0, defaultValue: 0 },
  { name: 'tenure_start', label: 'Tenure start', type: 'date' },
  { name: 'tenure_end', label: 'Tenure end', type: 'date' },
  {
    name: 'photo',
    type: 'image',
    label: 'Photograph',
    previewKey: 'photo_url',
    hint: 'Shown publicly on the Administration section of the home page.',
  },
  { name: 'message', label: 'Public message', type: 'textarea', rows: 6 },
  { name: 'biography', label: 'Biography', type: 'textarea', rows: 4 },
]

/**
 * The principal's office.
 *
 * Two seats are administered here — principal and vice principal — because
 * both appear in the public Administration section and both are governed by
 * the same `principal.*` permission codes. Approvals and oversight below are
 * the office's internal work.
 */
export function PrincipalOffice() {
  useDocumentTitle('Administration')

  const toast = useToast()
  const { data, error, isLoading, refetch } = useApi(() => principalService.dashboard(), [])

  // `null` closed; otherwise `{ office, record }` — a record without an id is a new one.
  const [editing, setEditing] = useState(null)
  const [isSaving, setSaving] = useState(false)
  const form = useResourceForm(FIELDS, editing?.record?.id ? editing.record : null)

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const values = form.payload()
      const photo = form.values.photo
      const body = new FormData()
      Object.entries({ ...values, office: editing.office, is_current: true }).forEach(([key, value]) => {
        if (key !== 'photo' && value !== undefined && value !== null) body.append(key, value)
      })
      if (photo) body.append('photo', photo)

      if (editing.record?.id) {
        await principalService.patch(editing.record.id, body)
        toast.success('Profile updated.')
      } else {
        await principalService.create(body)
        toast.success('Administrator recorded.')
      }
      setEditing(null)
      refetch()
    } catch (caught) {
      form.setErrors(caught.errors ?? {})
      toast.error(caught.message)
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <LoadingState label="Loading the principal's office…" />

  return (
    <div>
      <PageHeader
        title="Administration"
        description="The principal and vice principal — public profiles, pending approvals and school oversight."
        actions={
          <a href="/#administration" target="_blank" rel="noreferrer">
            <Button variant="secondary" leftIcon={<ExternalLink className="h-4 w-4" />}>
              View the site
            </Button>
          </a>
        }
      />

      {error ? (
        <Alert type="error" title="Could not load this page" className="mb-6">
          {error.message}
        </Alert>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={ClipboardCheck}
          label="Pending approvals"
          value={formatNumber(data?.pending_approvals)}
          tone="gold"
        />
        <StatCard
          icon={FileWarning}
          label="Unpublished notices"
          value={formatNumber(data?.unpublished_notices)}
          tone="crimson"
        />
        <StatCard icon={GraduationCap} label="Active students" value={formatNumber(data?.total_students)} tone="brand" />
        <StatCard icon={Users} label="Active teachers" value={formatNumber(data?.total_teachers)} tone="violet" />
      </div>

      {/* The two public profiles */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        {OFFICES.map((office) => (
          <OfficeCard
            key={office.key}
            office={office}
            person={data?.[office.key]}
            onEdit={(record) => setEditing({ office: office.key, record: record ?? {} })}
          />
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {/* Pending approvals by category */}
        <Card>
          <CardHeader title="Approvals awaiting a decision" />
          <ul className="divide-y divide-slate-100">
            {(data?.pending_by_category ?? []).length === 0 ? (
              <li>
                <EmptyState icon={ClipboardCheck} title="Nothing pending" className="py-10" />
              </li>
            ) : (
              data.pending_by_category.map((row) => (
                <li key={row.category} className="flex items-center justify-between px-5 py-3.5">
                  <span className="text-sm text-slate-700">{humanise(row.category)}</span>
                  <Badge tone="warning">{row.total}</Badge>
                </li>
              ))
            )}
          </ul>
        </Card>

        {/* Recent approvals */}
        <Card className="lg:col-span-2">
          <CardHeader title="Recent approval requests" />
          <ul className="divide-y divide-slate-100">
            {(data?.recent_approvals ?? []).length === 0 ? (
              <li>
                <EmptyState icon={ClipboardCheck} title="No requests yet" className="py-10" />
              </li>
            ) : (
              data.recent_approvals.map((approval) => (
                <li key={approval.id} className="flex flex-wrap items-center justify-between gap-3 px-5 py-3.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-800">{approval.title}</p>
                    <p className="text-xs text-slate-500">
                      {approval.category_display} · {approval.requested_by_name ?? 'Unknown'} ·{' '}
                      {formatDate(approval.created_at)}
                    </p>
                  </div>
                  <StatusBadge status={approval.status} label={approval.status_display} />
                </li>
              ))
            )}
          </ul>
        </Card>
      </div>

      <Modal
        isOpen={editing !== null}
        onClose={() => setEditing(null)}
        title={
          editing?.record?.id
            ? `Edit the ${OFFICES.find((office) => office.key === editing.office)?.label.toLowerCase()}'s profile`
            : `Record the ${OFFICES.find((office) => office.key === editing?.office)?.label.toLowerCase() ?? 'administrator'}`
        }
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditing(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="principal-form" isLoading={isSaving}>
              Save
            </Button>
          </div>
        }
      >
        <form id="principal-form" onSubmit={handleSave} noValidate>
          <ResourceForm
            fields={FIELDS}
            values={form.values}
            errors={form.errors}
            onChange={form.change}
            record={editing?.record}
          />
        </form>
      </Modal>
    </div>
  )
}

function OfficeCard({ office, person, onEdit }) {
  return (
    <Card>
      <CardHeader
        title={office.label}
        description="Shown publicly in the Administration section of the home page."
        action={
          <Can permission="principal.update">
            <Button
              size="sm"
              variant={person ? 'secondary' : 'primary'}
              leftIcon={<Pencil className="h-3.5 w-3.5" />}
              onClick={() => onEdit(person)}
            >
              {person ? 'Edit' : 'Record'}
            </Button>
          </Can>
        }
      />
      <CardBody>
        {person ? (
          <div>
            <div className="flex flex-wrap items-center gap-4">
              <Avatar src={person.photo_url} name={person.full_name} size="lg" />
              <div className="min-w-0">
                <p className="truncate text-lg font-semibold text-slate-900">{person.full_name}</p>
                <p className="text-sm text-brand-600">{person.designation || person.office_display}</p>
                {person.qualification ? (
                  <p className="mt-0.5 text-xs text-slate-500">{person.qualification}</p>
                ) : null}
              </div>
              <div className="ml-auto flex flex-col items-end gap-1.5">
                <Badge tone="success">In office</Badge>
                {person.tenure_start ? (
                  <span className="text-xs text-slate-500">Since {formatDate(person.tenure_start)}</span>
                ) : null}
              </div>
            </div>

            <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-5 text-sm sm:grid-cols-3">
              {[
                ['Email', person.email || '—'],
                ['Phone', person.phone || '—'],
                ['Experience', `${person.experience_years ?? 0} years`],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
                  <dd className="mt-0.5 truncate text-slate-800">{value}</dd>
                </div>
              ))}
            </dl>

            {person.message ? (
              <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Public message</p>
                <p className="mt-2 line-clamp-4 whitespace-pre-line text-sm leading-relaxed text-slate-700">
                  {person.message}
                </p>
              </div>
            ) : null}
          </div>
        ) : (
          <EmptyState
            icon={BadgeCheck}
            title={`No ${office.label.toLowerCase()} recorded`}
            description={`${office.description} Record them so their profile appears on the public site.`}
            action={
              <Can permission="principal.update">
                <Button onClick={() => onEdit(null)}>Record {office.label.toLowerCase()}</Button>
              </Can>
            }
          />
        )}
      </CardBody>
    </Card>
  )
}

export default PrincipalOffice
