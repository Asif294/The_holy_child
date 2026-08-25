import { useMemo, useState } from 'react'
import { KeyRound, Pencil, Plus, Search, Trash2, UserCog } from 'lucide-react'

import Avatar from '@/components/ui/Avatar'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Select } from '@/components/ui/Input'
import Modal, { ConfirmDialog } from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import useApi from '@/hooks/useApi'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import { roleService, userService } from '@/services'
import { formatDateTime } from '@/utils/formatters'

const GENDER_OPTIONS = [
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
]

export function Users() {
  useDocumentTitle('Users')

  const toast = useToast()
  const { user: currentUser } = useAuth()
  const list = usePaginatedList(userService)
  const { data: roles } = useApi(() => roleService.all(), [], { initialData: [] })

  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [isSaving, setSaving] = useState(false)
  const [isDeleting, setDeleting_] = useState(false)

  const roleOptions = useMemo(() => (roles ?? []).map((role) => ({ value: role.id, label: role.name })), [roles])

  const fields = useMemo(
    () => [
      { name: 'full_name', label: 'Full name', required: true },
      { name: 'email', label: 'Email address', type: 'email', required: true, placeholder: 'name@holychildschool.edu.bd' },
      { name: 'username', label: 'Username', hint: 'Derived from the email when left blank.' },
      { name: 'phone', label: 'Phone', type: 'tel', placeholder: '+8801700000000' },
      {
        name: 'password',
        label: editing?.id ? 'New password' : 'Password',
        type: 'password',
        required: !editing?.id,
        hint: editing?.id ? 'Leave blank to keep the current password.' : 'At least 8 characters.',
      },
      { name: 'role_id', label: 'Role', type: 'select', options: roleOptions, required: true },
      { name: 'gender', label: 'Gender', type: 'select', options: GENDER_OPTIONS },
      { name: 'date_of_birth', label: 'Date of birth', type: 'date' },
      { name: 'address', label: 'Address', type: 'textarea' },
      { name: 'is_active', label: 'Account is active', type: 'checkbox', defaultValue: true },
    ],
    [editing, roleOptions],
  )

  const formRecord = useMemo(
    () =>
      editing?.id
        ? { ...editing, role_id: editing.role?.id ?? '', password: '' }
        : null,
    [editing],
  )
  const form = useResourceForm(fields, formRecord)

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = form.payload()
      // `is_active` is a boolean — payload() drops falsey values, so restore it.
      payload.is_active = Boolean(form.values.is_active)

      if (editing?.id) {
        if (!payload.password) delete payload.password
        await userService.patch(editing.id, payload)
        toast.success('User updated.')
      } else {
        await userService.create(payload)
        toast.success('User created.')
      }
      setEditing(null)
      list.reload()
    } catch (error) {
      form.setErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    setDeleting_(true)
    try {
      await userService.remove(deleting.id)
      toast.success('User deactivated.')
      setDeleting(null)
      list.reload()
    } catch (error) {
      toast.error(error.message)
    } finally {
      setDeleting_(false)
    }
  }

  const columns = [
    {
      key: 'full_name',
      header: 'User',
      render: (row) => (
        <div className="flex items-center gap-3">
          <Avatar src={row.profile_image_url} name={row.full_name} size="sm" />
          <div className="min-w-0">
            <p className="truncate font-medium text-slate-900">
              {row.full_name}
              {row.id === currentUser?.id ? <span className="ml-1.5 text-xs text-slate-400">(you)</span> : null}
            </p>
            <p className="truncate text-xs text-slate-500">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      render: (row) => (row.role ? <Badge tone="brand">{row.role.name}</Badge> : <Badge>No role</Badge>),
    },
    {
      key: 'permissions',
      header: 'Permissions',
      render: (row) => (
        <span className="inline-flex items-center gap-1.5 text-sm text-slate-600">
          <KeyRound className="h-3.5 w-3.5 text-slate-400" />
          {row.permissions?.length ?? 0}
        </span>
      ),
    },
    { key: 'phone', header: 'Phone', render: (row) => row.phone || '—' },
    { key: 'last_login', header: 'Last sign-in', render: (row) => formatDateTime(row.last_login) },
    {
      key: 'is_active',
      header: 'Status',
      render: (row) =>
        row.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="danger">Inactive</Badge>,
    },
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-24',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Can permission="user.update">
            <button
              type="button"
              onClick={() => setEditing(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-brand-50 hover:text-brand-600"
              aria-label={`Edit ${row.full_name}`}
            >
              <Pencil className="h-4 w-4" />
            </button>
          </Can>
          <Can permission="user.delete">
            <button
              type="button"
              onClick={() => setDeleting(row)}
              disabled={row.id === currentUser?.id}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-crimson-50 hover:text-crimson-600 disabled:cursor-not-allowed disabled:opacity-30"
              aria-label={`Deactivate ${row.full_name}`}
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </Can>
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader
        title="Users"
        description="Staff and student accounts, and the role each one inherits its permissions from."
        actions={
          <Can permission="user.create">
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => setEditing({})}>
              Add user
            </Button>
          </Can>
        }
      />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={UserCog}
        emptyTitle="No users found"
        emptyDescription="Create an account and assign it a role."
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder="Search name, email or phone…"
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label="Search users"
            />
            <Select
              className="w-auto min-w-[10rem]"
              placeholder="All roles"
              options={roleOptions}
              value={list.filters.role ?? ''}
              onChange={(event) => list.setFilter('role', event.target.value)}
              aria-label="Filter by role"
            />
          </div>
        }
        pagination={{
          page: list.page,
          totalPages: list.totalPages,
          count: list.count,
          pageSize: list.pageSize,
          onChange: list.setPage,
        }}
      />

      <Modal
        isOpen={editing !== null}
        onClose={() => setEditing(null)}
        title={editing?.id ? 'Edit user' : 'Add a user'}
        description={
          editing?.id
            ? editing.email
            : 'Administrators may assign any role here — self-registration always uses the default role instead.'
        }
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setEditing(null)} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="user-form" isLoading={isSaving}>
              {editing?.id ? 'Save changes' : 'Create user'}
            </Button>
          </div>
        }
      >
        <form id="user-form" onSubmit={handleSave} noValidate>
          <ResourceForm fields={fields} values={form.values} errors={form.errors} onChange={form.change} />
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title="Deactivate this account?"
        description={`${deleting?.full_name ?? ''} will no longer be able to sign in. Their historical records are kept.`}
        confirmLabel="Deactivate"
      />
    </div>
  )
}

export default Users
