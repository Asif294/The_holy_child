import cn from '@/utils/cn'

export function Table({ className, children }) {
  return (
    <div className="scrollbar-slim w-full overflow-x-auto">
      <table className={cn('w-full min-w-[640px] border-collapse text-left text-sm', className)}>{children}</table>
    </div>
  )
}

export function THead({ children }) {
  return <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">{children}</thead>
}

export function TH({ className, children, ...props }) {
  return (
    <th scope="col" className={cn('whitespace-nowrap px-5 py-3 font-semibold', className)} {...props}>
      {children}
    </th>
  )
}

export function TBody({ children }) {
  return <tbody className="divide-y divide-slate-100">{children}</tbody>
}

export function TR({ className, children, ...props }) {
  return (
    <tr className={cn('transition-colors hover:bg-slate-50/70', className)} {...props}>
      {children}
    </tr>
  )
}

export function TD({ className, children, ...props }) {
  return (
    <td className={cn('px-5 py-3.5 align-middle text-slate-700', className)} {...props}>
      {children}
    </td>
  )
}

export default Table
