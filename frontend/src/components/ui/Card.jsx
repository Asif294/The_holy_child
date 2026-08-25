import cn from '@/utils/cn'

export function Card({ className, children, ...props }) {
  return (
    <div className={cn('card', className)} {...props}>
      {children}
    </div>
  )
}

export function CardHeader({ title, description, action, className, children }) {
  return (
    <div className={cn('flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-5 py-4', className)}>
      <div className="min-w-0">
        {title ? <h3 className="text-base font-semibold text-slate-900">{title}</h3> : null}
        {description ? <p className="mt-0.5 text-sm text-slate-500">{description}</p> : null}
        {children}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}

export function CardBody({ className, children }) {
  return <div className={cn('p-5', className)}>{children}</div>
}

export function CardFooter({ className, children }) {
  return <div className={cn('border-t border-slate-200 px-5 py-3.5', className)}>{children}</div>
}

export default Card
