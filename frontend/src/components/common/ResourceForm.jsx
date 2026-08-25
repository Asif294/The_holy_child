import { useEffect, useState } from 'react'

import Input, { Select, Textarea } from '@/components/ui/Input'
import cn from '@/utils/cn'

/**
 * Renders a form from a field description list.
 *
 * Supported types: text, email, tel, number, date, time, textarea, select,
 * checkbox. Anything more bespoke than that belongs in a hand-written form,
 * not here.
 */
export function ResourceForm({ fields, values, errors = {}, onChange, id, className }) {
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

/** Seeds form state from a record (or the field defaults when creating). */
export function useResourceForm(fields, record) {
  const [values, setValues] = useState({})
  const [errors, setErrors] = useState({})

  useEffect(() => {
    const next = {}
    for (const field of fields) {
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
