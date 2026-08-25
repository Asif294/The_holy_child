import { useCallback, useEffect, useMemo, useState } from 'react'
import { Lock, Pencil, Plus, Search, ShieldCheck, Trash2, Users } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Badge from '@/components/ui/Badge'
import Button from '@/components/ui/Button'
import Input, { Textarea } from '@/components/ui/Input'
import Modal, { ConfirmDialog } from '@/components/ui/Modal'
import { LoadingState } from '@/components/ui/Spinner'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useAuth from '@/hooks/useAuth'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import { permissionService, roleService } from '@/services'
import { formatDate } from '@/utils/formatters'

/**
 * The permission matrix.
 *
 * Grouped exactly as the API returns it — group → module → permission — so the
 * checkbox grid always mirrors whatever the backend catalogue currently holds.
 */
function PermissionMatrix({ groups, selected, onToggle, onToggleModule, onToggleGroup, disabled }) {
  return (
    <div className="space-y-5">
      {groups.map((group) => {
        const groupCodes = group.modules.flatMap((module) => module.permissions.map((p) => p.code))
        const allSelected = groupCodes.every((code) => selected.has(code))

        return (
          <section key={group.group} className="rounded-xl border border-slate-200">
            <header className="flex items-center justify-between gap-3 rounded-t-xl border-b border-slate-200 bg-slate-50 px-4 py-2.5">
              <h3 className="text-sm font-semibold text-slate-800">{group.group}</h3>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onToggleGroup(groupCodes, !allSelected)}
                className="text-xs font-medium text-brand-600 transition-colors hover:text-brand-700 disabled:opacity-50"
              >
                {allSelected ? 'Clear all' : 'Select all'}
              </button>
            </header>

            <div className="divide-y divide-slate-100">
              {group.modules.map((module) => {
                const moduleCodes = module.permissions.map((p) => p.code)
                const moduleAll = moduleCodes.every((code) => selected.has(code))

                return (
                  <div key={module.module} className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3">
                    <button
                      type="button"
                      disabled={disabled}
                      onClick={() => onToggleModule(moduleCodes, !moduleAll)}
                      className="w-40 shrink-0 text-left text-sm font-medium text-slate-700 transition-colors hover:text-brand-600 disabled:opacity-50"
                    >
                      {module.label}
                    </button>

                    <div className="flex flex-wrap gap-x-5 gap-y-2">
                      {module.permissions.map((permission) => (
                        <label
                          key={permission.code}
                          className="flex cursor-pointer items-center gap-2 text-sm text-slate-600"
                          title={permission.code}
                        >
                          <input
                            type="checkbox"
                            disabled={disabled}
                            checked={selected.has(permission.code)}
                            onChange={() => onToggle(permission.code)}
                            className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500 disabled:opacity-50"
                          />
                          <span className="capitalize">{permission.action}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        )
      })}
    </div>
  )
}

export function Roles() {
  useDocumentTitle('Roles')

  const toast = useToast()
  const { refreshUser, user } = useAuth()
  const list = usePaginatedList(roleService)
  const { data: groups, isLoading: groupsLoading } = useApi(() => permissionService.grouped(), [], {
    initialData: [],
  })

  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [form, setForm] = useState({ name: '', description: '' })
  const [selected, setSelected] = useState(new Set())
  const [errors, setErrors] = useState({})
  const [isSaving, setSaving] = useState(false)
  const [isDeleting, setDeleting_] = useState(false)
  const [isLoadingRole, setLoadingRole] = useState(false)

  const isSuperAdminRole = editing?.slug === 'super-admin'
  const totalCodes = useMemo(
    () => groups.flatMap((group) => group.modules.flatMap((module) => module.permissions)).length,
    [groups],
  )

  useEffect(() => {
    if (editing === null) {
      setForm({ name: '', description: '' })
      setSelected(new Set())
      setErrors({})
    }
  }, [editing])

  const openCreate = useCallback(() => {
    setForm({ name: '', description: '' })
    setSelected(new Set())
    setErrors({})
    setEditing({})
  }, [])

  const openEdit = useCallback(
    async (row) => {
      setEditing(row)
      setLoadingRole(true)
      try {
        const detail = await roleService.retrieve(row.id)
        setEditing(detail)
        setForm({ name: detail.name, description: detail.description ?? '' })
        setSelected(new Set(detail.permissions ?? []))
      } catch (error) {
        toast.error(error.message)
        setEditing(null)
      } finally {
        setLoadingRole(false)
      }
    },
    [toast],
  )

  function toggle(code) {
    setSelected((current) => {
      const next = new Set(current)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  function toggleMany(codes, shouldSelect) {
    setSelected((current) => {
      const next = new Set(current)
      for (const code of codes) {
        if (shouldSelect) next.add(code)
        else next.delete(code)
      }
      return next
    })
  }

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setErrors({})
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description,
        ...(isSuperAdminRole ? {} : { permissions: [...selected] }),
      }

      if (editing?.id) {
        await roleService.patch(editing.id, payload)
        toast.success('Role updated.')
      } else {
        await roleService.create(payload)
        toast.success('Role created.')
      }

      setEditing(null)
      list.reload()
      // The signed-in user may have just had their own role edited.
      if (editing?.id && user?.role?.id === editing.id) await refreshUser()
    } catch (error) {
      setErrors(error.errors ?? {})
      toast.error(error.message)
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    setDeleting_(true)
    try {
      await roleService.remove(deleting.id)
      toast.success('Role deleted.')
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
      key: 'name',
      header: 'Role',
      render: (row) => (
        <div className="flex items-center gap-3">
          <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
            {row.is_system ? <Lock className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
          </span>
          <div className="min-w-0">
            <p className="font-medium text-slate-900">{row.name}</p>
            <p className="truncate text-xs text-slate-500">{row.description || row.slug}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'permission_count',
      header: 'Permissions',
      render: (row) => (
        <Badge tone="brand">
          {row.permission_count} / {totalCodes || '—'}
        </Badge>
      ),
    },
    {
      key: 'user_count',
      header: 'Users',
      render: (row) => (
        <span className="inline-flex items-center gap-1.5 text-slate-600">
          <Users className="h-3.5 w-3.5 text-slate-400" />
          {row.user_count}
        </span>
      ),
    },
    {
      key: 'is_system',
      header: 'Type',
      render: (row) => (row.is_system ? <Badge tone="warning">System</Badge> : <Badge tone="neutral">Custom</Badge>),
    },
    { key: 'created_at', header: 'Created', render: (row) => formatDate(row.created_at) },
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-24',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Can permission="role.update">
            <button
              type="button"
              onClick={() => openEdit(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-brand-50 hover:text-brand-600"
              aria-label={`Edit ${row.name}`}
            >
              <Pencil className="h-4 w-4" />
            </button>
          </Can>
          <Can permission="role.delete">
            <button
              type="button"
              onClick={() => setDeleting(row)}
              disabled={row.is_system}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-crimson-50 hover:text-crimson-600 disabled:cursor-not-allowed disabled:opacity-30"
              aria-label={`Delete ${row.name}`}
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
        title="Roles"
        description="Compose roles from granular permissions. Assign one to a user and their access — and their navigation — follows immediately."
        actions={
          <Can permission="role.create">
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Create role
            </Button>
          </Can>
        }
      />

      <DataTable
        columns={columns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyIcon={ShieldCheck}
        emptyTitle="No roles yet"
        emptyDescription="Create your first role and pick the permissions it carries."
        toolbar={
          <Input
            containerClassName="w-full sm:max-w-xs"
            placeholder="Search roles…"
            leftIcon={<Search className="h-4 w-4" />}
            value={list.search}
            onChange={(event) => list.setSearch(event.target.value)}
            aria-label="Search roles"
          />
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
        title={editing?.id ? `Edit role — ${editing.name ?? ''}` : 'Create a role'}
        description="Tick the capabilities this role should carry. Django enforces every one of them on the API."
        size="xl"
        footer={
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-sm text-slate-500">
              <span className="font-semibold text-slate-800">{selected.size}</span> of {totalCodes} permissions selected
            </p>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setEditing(null)} disabled={isSaving}>
                Cancel
              </Button>
              <Button type="submit" form="role-form" isLoading={isSaving}>
                {editing?.id ? 'Save changes' : 'Create role'}
              </Button>
            </div>
          </div>
        }
      >
        <form id="role-form" onSubmit={handleSave} noValidate>
          {editing?.is_system ? (
            <Alert type="warning" className="mb-4">
              This is a system role. Its name is fixed
              {isSuperAdminRole ? ' and it always holds every permission.' : '.'}
            </Alert>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Role name"
              required
              placeholder="Librarian"
              value={form.name}
              disabled={editing?.is_system}
              onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
              error={Array.isArray(errors.name) ? errors.name[0] : errors.name}
            />
            <Input
              label="Slug"
              value={editing?.slug ?? '— generated from the name —'}
              disabled
              hint="Generated automatically and never changes."
            />
            <div className="sm:col-span-2">
              <Textarea
                label="Description"
                rows={2}
                placeholder="What this role is responsible for."
                value={form.description}
                onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
              />
            </div>
          </div>

          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-900">Permissions</h3>
              {!isSuperAdminRole ? (
                <button
                  type="button"
                  onClick={() => setSelected(new Set())}
                  className="text-xs font-medium text-slate-500 hover:text-crimson-600"
                >
                  Clear all
                </button>
              ) : null}
            </div>

            {isLoadingRole || groupsLoading ? (
              <LoadingState label="Loading permissions…" />
            ) : (
              <PermissionMatrix
                groups={groups}
                selected={isSuperAdminRole ? new Set(groups.flatMap((g) => g.modules.flatMap((m) => m.permissions.map((p) => p.code)))) : selected}
                onToggle={toggle}
                onToggleModule={toggleMany}
                onToggleGroup={toggleMany}
                disabled={isSuperAdminRole}
              />
            )}
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title="Delete this role?"
        description={`"${deleting?.name ?? ''}" will be removed. Roles still assigned to users cannot be deleted — reassign those users first.`}
        confirmLabel="Delete role"
      />
    </div>
  )
}

export default Roles
