import { useCallback, useMemo, useState } from 'react'
import { Pencil, Plus, Search, Trash2 } from 'lucide-react'

import Button from '@/components/ui/Button'
import Input, { Select } from '@/components/ui/Input'
import Modal, { ConfirmDialog } from '@/components/ui/Modal'
import Can from '@/components/common/Can'
import DataTable from '@/components/common/DataTable'
import PageHeader from '@/components/common/PageHeader'
import ResourceForm, { useResourceForm } from '@/components/common/ResourceForm'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import usePaginatedList from '@/hooks/usePaginatedList'
import useToast from '@/hooks/useToast'
import useUniqueCheck from '@/hooks/useUniqueCheck'

/**
 * A complete list-plus-modal CRUD screen driven by declarations.
 *
 * The reference-data modules (subjects, classes, fee heads, exam types…) are
 * genuinely identical screens over different tables, so they share this rather
 * than each repeating four hundred lines of the same wiring. Screens with real
 * behaviour of their own — attendance, roles, results — are written by hand.
 */
export function CrudPage({
  title,
  description,
  service,
  module,
  columns,
  fields,
  filters = [],
  singular = 'record',
  searchPlaceholder = 'Search…',
  emptyTitle,
  emptyDescription,
  toPayload = (values) => values,
  toFormValues = (record) => record,
  createDefaults,
  checkUnique,
  extraActions,
  rowActions,
}) {
  useDocumentTitle(title)

  const toast = useToast()
  const list = usePaginatedList(service)

  const [editing, setEditing] = useState(null) // null = closed, {} = create
  const [deleting, setDeleting] = useState(null)
  const [isSaving, setSaving] = useState(false)
  const [isDeleting, setDeleting_] = useState(false)

  // `editing` doubles as the form seed: the row when editing, and a fresh `{}`
  // when creating. Handing over that new object — rather than a shared `null` —
  // re-seeds the form every time it opens, so cancelling a half-filled create
  // and starting again begins from the defaults instead of the old answers.
  const formRecord = useMemo(
    () => (editing && editing.id ? toFormValues(editing) : editing),
    [editing, toFormValues],
  )
  const form = useResourceForm(fields, formRecord)

  // A form with a file in it has to go out as multipart; one without stays JSON.
  const hasFileField = useMemo(() => fields.some((field) => field.type === 'image'), [fields])

  // Fields declared `unique: true` are checked against the register as they are
  // typed, so a code that is already taken is called out there rather than at
  // the save. `checkUnique` is the service call that answers for this resource.
  const uniqueFields = useMemo(
    () => fields.filter((field) => field.unique).map((field) => field.name),
    [fields],
  )
  const check = useUniqueCheck(checkUnique, form.setErrors)

  const handleChange = useCallback(
    (name, value) => {
      form.change(name, value)
      if (uniqueFields.includes(name)) check(name, value, { exclude: editing?.id })
    },
    [form, uniqueFields, check, editing],
  )

  const closeForm = useCallback(() => setEditing(null), [])

  /**
   * Opens a blank form, then fills in whatever the server wants to suggest —
   * a generated employee ID, say. The modal opens immediately either way: the
   * suggestion arriving late, or not at all, just leaves a field to type into.
   */
  async function openCreate() {
    setEditing({})
    if (!createDefaults) return
    try {
      const defaults = await createDefaults()
      if (defaults) form.setValues((current) => ({ ...current, ...defaults }))
    } catch {
      // Not worth a toast — the field is editable, so the clerk can type one.
    }
  }

  /** JSON by default; multipart once the form can carry a file. */
  function bodyFor(payload) {
    if (!hasFileField) return payload
    const body = new FormData()
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) body.append(key, value)
    })
    return body
  }

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    try {
      const payload = bodyFor(toPayload(form.payload(), form.values))
      if (editing?.id) {
        await service.patch(editing.id, payload)
        toast.success(`${title.replace(/s$/, '')} updated.`)
      } else {
        await service.create(payload)
        toast.success(`${title.replace(/s$/, '')} created.`)
      }
      closeForm()
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
      await service.remove(deleting.id)
      toast.success('Deleted successfully.')
      setDeleting(null)
      list.reload()
    } catch (error) {
      toast.error(error.message)
    } finally {
      setDeleting_(false)
    }
  }

  const tableColumns = [
    ...columns,
    {
      key: '__actions',
      header: '',
      headerClassName: 'w-24',
      className: 'text-right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          {rowActions?.(row, list.reload)}
          <Can permission={`${module}.update`}>
            <button
              type="button"
              onClick={() => setEditing(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-brand-50 hover:text-brand-600"
              aria-label={`Edit ${row.name ?? row.title ?? singular}`}
            >
              <Pencil className="h-4 w-4" />
            </button>
          </Can>
          <Can permission={`${module}.delete`}>
            <button
              type="button"
              onClick={() => setDeleting(row)}
              className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-crimson-50 hover:text-crimson-600"
              aria-label={`Delete ${row.name ?? row.title ?? singular}`}
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
        title={title}
        description={description}
        actions={
          <>
            {extraActions}
            <Can permission={`${module}.create`}>
              <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
                Add {singular}
              </Button>
            </Can>
          </>
        }
      />

      <DataTable
        columns={tableColumns}
        rows={list.items}
        isLoading={list.isLoading}
        error={list.error}
        emptyTitle={emptyTitle ?? `No ${title.toLowerCase()} yet`}
        emptyDescription={emptyDescription ?? `Add your first ${singular} to get started.`}
        toolbar={
          <div className="flex flex-wrap items-center gap-3">
            <Input
              containerClassName="w-full sm:max-w-xs"
              placeholder={searchPlaceholder}
              leftIcon={<Search className="h-4 w-4" />}
              value={list.search}
              onChange={(event) => list.setSearch(event.target.value)}
              aria-label={searchPlaceholder}
            />
            {filters.map((filter) => (
              <Select
                key={filter.name}
                className="w-auto min-w-[10rem]"
                placeholder={filter.placeholder}
                options={filter.options}
                value={list.filters[filter.name] ?? ''}
                onChange={(event) => list.setFilter(filter.name, event.target.value)}
                aria-label={filter.placeholder}
              />
            ))}
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
        onClose={closeForm}
        title={editing?.id ? `Edit ${singular}` : `Add ${singular}`}
        size="lg"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeForm} disabled={isSaving}>
              Cancel
            </Button>
            <Button type="submit" form="crud-form" isLoading={isSaving}>
              {editing?.id ? 'Save changes' : `Create ${singular}`}
            </Button>
          </div>
        }
      >
        <form id="crud-form" onSubmit={handleSave} noValidate>
          <ResourceForm
            fields={fields}
            values={form.values}
            errors={form.errors}
            onChange={handleChange}
            record={editing}
          />
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={Boolean(deleting)}
        onClose={() => setDeleting(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title={`Delete this ${singular}?`}
        description={`"${deleting?.name ?? deleting?.title ?? ''}" will be deactivated. Existing records that reference it stay intact.`}
        confirmLabel="Delete"
      />
    </div>
  )
}

export default CrudPage
