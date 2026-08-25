import { useEffect, useState } from 'react'
import { ImageUp, X } from 'lucide-react'

import Input, { Select, Textarea } from '@/components/ui/Input'
import cn from '@/utils/cn'

/**
 * Renders a form from a field description list.
 *
 * Supported types: text, email, tel, number, date, time, textarea, select,
 * checkbox and image. Anything more bespoke than that belongs in a
 * hand-written form, not here.
 *
 * `record` is the row being edited, used only so an image field can show what
 * is already stored (`field.previewKey`, e.g. `image_url`) beside the picker.
 */
export function ResourceForm({ fields, values, errors = {}, onChange, record, id, className }) {
  function errorFor(name) {
    const value = errors[name]
    return Array.isArray(value) ? value[0] : value
  }

  return (
    <div id={id} className={cn('grid gap-4 sm:grid-cols-2', className)}>
      {fields.map((field) => {
        const common = {
          key: field.name,
          label: field.label,
          required: field.required,
          error: errorFor(field.name),
          hint: field.hint,
          disabled: field.disabled,
          placeholder: field.placeholder,
        }
        const wrapper = field.fullWidth ? 'sm:col-span-2' : ''

        if (field.type === 'image') {
          return (
            <div key={field.name} className={cn('sm:col-span-2', field.halfWidth && 'sm:col-span-1')}>
              <ImageField
                label={field.label}
                hint={field.hint}
                required={field.required}
                error={errorFor(field.name)}
                file={values[field.name]}
                existingUrl={record?.[field.previewKey ?? `${field.name}_url`]}
                onChange={(file) => onChange(field.name, file)}
              />
            </div>
          )
        }

        if (field.type === 'checkbox') {
          return (
            <label
              key={field.name}
              className={cn('flex items-center gap-2.5 self-end pb-2.5 text-sm text-slate-700', wrapper)}
            >
              <input
                type="checkbox"
                checked={Boolean(values[field.name])}
                onChange={(event) => onChange(field.name, event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
              />
              {field.label}
            </label>
          )
        }

        if (field.type === 'textarea') {
          return (
            <div key={field.name} className="sm:col-span-2">
              <Textarea
                {...common}
                rows={field.rows ?? 3}
                value={values[field.name] ?? ''}
                onChange={(event) => onChange(field.name, event.target.value)}
              />
            </div>
          )
        }

        if (field.type === 'select') {
          return (
            <div key={field.name} className={wrapper}>
              <Select
                {...common}
                options={field.options ?? []}
                placeholder={field.placeholder ?? 'Select…'}
                value={values[field.name] ?? ''}
                onChange={(event) => onChange(field.name, event.target.value)}
              />
            </div>
          )
        }

        return (
          <div key={field.name} className={wrapper}>
            <Input
              {...common}
              type={field.type ?? 'text'}
              min={field.min}
              max={field.max}
              step={field.step}
              value={values[field.name] ?? ''}
              onChange={(event) => onChange(field.name, event.target.value)}
            />
          </div>
        )
      })}
    </div>
  )
}

/**
 * A file picker that shows what is already stored.
 *
 * Leaving it untouched keeps the existing file — the API only replaces an
 * image when one is actually uploaded — so the control says so rather than
 * looking like an empty field that will blank the record.
 */
export function ImageField({ label, hint, required, error, file, existingUrl, onChange }) {
  const [preview, setPreview] = useState(null)

  useEffect(() => {
    if (!file) {
      setPreview(null)
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const shown = preview || existingUrl

  return (
    <div className="w-full">
      {label ? (
        <span className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required ? <span className="ml-0.5 text-crimson-600">*</span> : null}
        </span>
      ) : null}

      <div className="flex items-center gap-4">
        <div className="grid h-20 w-28 shrink-0 place-items-center overflow-hidden rounded-lg border border-dashed border-slate-300 bg-slate-50">
          {shown ? (
            <img src={shown} alt="" className="h-full w-full object-cover" />
          ) : (
            <ImageUp className="h-5 w-5 text-slate-400" aria-hidden="true" />
          )}
        </div>

        <div className="min-w-0 flex-1">
          <label className="inline-flex h-9 cursor-pointer items-center rounded-lg border border-slate-300 bg-white px-3 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50">
            {shown ? 'Choose a different image' : 'Choose an image'}
            <input
              type="file"
              accept="image/*"
              className="sr-only"
              onChange={(event) => onChange(event.target.files?.[0] ?? null)}
            />
          </label>

          {file ? (
            <button
              type="button"
              onClick={() => onChange(null)}
              className="ml-2 inline-flex h-9 items-center gap-1 rounded-lg px-2 text-sm text-slate-500 transition-colors hover:text-crimson-600"
            >
              <X className="h-3.5 w-3.5" /> Clear
            </button>
          ) : null}

          <p className="mt-1.5 truncate text-xs text-slate-500">
            {file
              ? file.name
              : existingUrl
                ? 'An image is already stored. Choose a new one to replace it.'
                : hint || 'PNG or JPG. Wide images work best.'}
          </p>
        </div>
      </div>

      {error ? <p className="mt-1.5 text-xs font-medium text-crimson-600">{error}</p> : null}
    </div>
  )
}

/** Seeds form state from a record (or the field defaults when creating). */
export function useResourceForm(fields, record) {
  const [values, setValues] = useState({})
  const [errors, setErrors] = useState({})

  useEffect(() => {
    const next = {}
    for (const field of fields) {
      if (field.type === 'image') {
        // An image field holds a newly picked File, never the stored URL:
        // "nothing chosen" has to mean "leave the stored file alone".
        next[field.name] = null
        continue
      }
      const raw = record ? record[field.name] : undefined
      next[field.name] = raw ?? field.defaultValue ?? (field.type === 'checkbox' ? false : '')
    }
    setValues(next)
    setErrors({})
  }, [fields, record])

  function change(name, value) {
    setValues((current) => ({ ...current, [name]: value }))
    setErrors((current) => ({ ...current, [name]: undefined }))
  }

  /** Strips blanks so DRF sees an omitted optional field rather than "". */
  function payload() {
    return Object.fromEntries(
      Object.entries(values).filter(([, value]) => value !== '' && value !== undefined && value !== null),
    )
  }

  return { values, errors, setErrors, change, payload, setValues }
}

export default ResourceForm
