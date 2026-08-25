import { useState } from 'react'
import { BadgeCheck, ClipboardCheck, FileWarning, GraduationCap, Pencil, Users } from 'lucide-react'

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

const FIELDS = [
  { name: 'full_name', label: 'Full name', required: true, placeholder: 'Md. Abdul Karim' },
  { name: 'designation', label: 'Designation', defaultValue: 'Principal' },
  { name: 'email', label: 'Email', type: 'email' },
  { name: 'phone', label: 'Phone', type: 'tel' },
  { name: 'qualification', label: 'Qualification', placeholder: 'M.A. in English, B.Ed.' },
  { name: 'experience_years', label: 'Years of experience', type: 'number', min: 0, defaultValue: 0 },
  { name: 'tenure_start', label: 'Tenure start', type: 'date' },
  { name: 'tenure_end', label: 'Tenure end', type: 'date' },
  { name: 'message', label: 'Message from the Principal', type: 'textarea', rows: 6 },
  { name: 'biography', label: 'Biography', type: 'textarea', rows: 4 },
]

export function PrincipalOffice() {
  useDocumentTitle("Principal's Office")

  const toast = useToast()
  const { data, error, isLoading, refetch } = useApi(() => principalService.dashboard(), [])

  const [editing, setEditing] = useState(null)
  const [isSaving, setSaving] = useState(false)
  const form = useResourceForm(FIELDS, editing?.id ? editing : null)

  const principal = data?.principal

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = { ...form.payload(), is_current: true }
      if (editing?.id) {
        await principalService.patch(editing.id, payload)
        toast.success("Principal's profile updated.")
      } else {
        await principalService.create(payload)
        toast.success('Principal recorded.')
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
        title="Principal's Office"
        description="The head of institution — profile, public message, pending approvals and school oversight."
        actions={
          <Can permission="principal.update">
            <Button
              leftIcon={<Pencil className="h-4 w-4" />}
              onClick={() => setEditing(principal ?? {})}
              variant={principal ? 'secondary' : 'primary'}
            >
              {principal ? 'Edit profile' : 'Record principal'}
            </Button>
          </Can>
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

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {/* Profile */}
        <Card className="lg:col-span-2">
          <CardHeader title="Principal" description="Shown publicly on the school's landing page." />
          <CardBody>
            {principal ? (
              <div>
                <div className="flex flex-wrap items-center gap-4">
                  <Avatar src={principal.photo_url} name={principal.full_name} size="lg" />
                  <div>
                    <p className="text-lg font-semibold text-slate-900">{principal.full_name}</p>
                    <p className="text-sm text-brand-600">{principal.designation}</p>
                    {principal.qualification ? (
                      <p className="mt-0.5 text-xs text-slate-500">{principal.qualification}</p>
                    ) : null}
                  </div>
                  <div className="ml-auto flex flex-col items-end gap-1.5">
                    <Badge tone="success">Sitting principal</Badge>
                    <span className="text-xs text-slate-500">
                      Since {formatDate(principal.tenure_start)}
                    </span>
                  </div>
                </div>

                <dl className="mt-6 grid grid-cols-2 gap-4 border-t border-slate-100 pt-5 text-sm sm:grid-cols-3">
                  {[
                    ['Email', principal.email || '—'],
                    ['Phone', principal.phone || '—'],
                    ['Experience', `${principal.experience_years ?? 0} years`],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</dt>
                      <dd className="mt-0.5 text-slate-800">{value}</dd>
                    </div>
                  ))}
                </dl>

                {principal.message ? (
                  <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Message from the Principal
                    </p>
                    <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-slate-700">
                      {principal.message}
                    </p>
                  </div>
                ) : null}
              </div>
            ) : (
              <EmptyState
                icon={BadgeCheck}
                title="No principal recorded"
                description="Record the sitting principal so their message appears on the public site."
                action={
                  <Can permission="principal.update">
                    <Button onClick={() => setEditing({})}>Record principal</Button>
                  </Can>
                }
              />
            )}
          </CardBody>
        </Card>

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
      </div>

      {/* Recent approvals */}
      <Card className="mt-4">
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

      <Modal
        isOpen={editing !== null}
        onClose={() => setEditing(null)}
        title={editing?.id ? "Edit the principal's profile" : 'Record the principal'}
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
          <ResourceForm fields={FIELDS} values={form.values} errors={form.errors} onChange={form.change} />
        </form>
      </Modal>
    </div>
  )
}

export default PrincipalOffice
