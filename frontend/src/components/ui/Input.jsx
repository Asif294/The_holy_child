import { forwardRef, useId } from 'react'

import cn from '@/utils/cn'

export const Input = forwardRef(function Input(
  { label, error, hint, leftIcon, rightSlot, className, containerClassName, required, id, ...props },
  ref,
) {
  const generatedId = useId()
  const inputId = id || generatedId
  const describedBy = error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined

  return (
    <div className={cn('w-full', containerClassName)}>
      {label ? (
        <label htmlFor={inputId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required ? <span className="ml-0.5 text-crimson-600">*</span> : null}
        </label>
      ) : null}

      <div className="relative">
        {leftIcon ? (
          <span className="pointer-events-none absolute inset-y-0 left-0 flex w-10 items-center justify-center text-slate-400">
            {leftIcon}
          </span>
        ) : null}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={Boolean(error)}
          aria-describedby={describedBy}
          className={cn(
            'input-base',
            leftIcon && 'pl-10',
            rightSlot && 'pr-11',
            error && 'border-crimson-400 focus:border-crimson-500 focus:ring-crimson-500/20',
            className,
          )}
          {...props}
        />
        {rightSlot ? <span className="absolute inset-y-0 right-0 flex w-11 items-center justify-center">{rightSlot}</span> : null}
      </div>

      {error ? (
        <p id={`${inputId}-error`} className="mt-1.5 text-xs font-medium text-crimson-600">
          {error}
        </p>
      ) : hint ? (
        <p id={`${inputId}-hint`} className="mt-1.5 text-xs text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  )
})

export const Textarea = forwardRef(function Textarea(
  { label, error, hint, className, containerClassName, required, id, ...props },
  ref,
) {
  const generatedId = useId()
  const fieldId = id || generatedId

  return (
    <div className={cn('w-full', containerClassName)}>
      {label ? (
        <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required ? <span className="ml-0.5 text-crimson-600">*</span> : null}
        </label>
      ) : null}
      <textarea
        ref={ref}
        id={fieldId}
        rows={4}
        aria-invalid={Boolean(error)}
        className={cn('input-base resize-y', error && 'border-crimson-400 focus:border-crimson-500', className)}
        {...props}
      />
      {error ? <p className="mt-1.5 text-xs font-medium text-crimson-600">{error}</p> : null}
      {!error && hint ? <p className="mt-1.5 text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
})

export const Select = forwardRef(function Select(
  { label, error, hint, options = [], placeholder, className, containerClassName, required, id, children, ...props },
  ref,
) {
  const generatedId = useId()
  const fieldId = id || generatedId

  return (
    <div className={cn('w-full', containerClassName)}>
      {label ? (
        <label htmlFor={fieldId} className="mb-1.5 block text-sm font-medium text-slate-700">
          {label}
          {required ? <span className="ml-0.5 text-crimson-600">*</span> : null}
        </label>
      ) : null}
      <select
        ref={ref}
        id={fieldId}
        aria-invalid={Boolean(error)}
        className={cn('input-base cursor-pointer pr-9', error && 'border-crimson-400', className)}
        {...props}
      >
        {placeholder ? <option value="">{placeholder}</option> : null}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
        {children}
      </select>
      {error ? <p className="mt-1.5 text-xs font-medium text-crimson-600">{error}</p> : null}
      {!error && hint ? <p className="mt-1.5 text-xs text-slate-500">{hint}</p> : null}
    </div>
  )
})

export default Input
