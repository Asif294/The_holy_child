import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'

import cn from '@/utils/cn'

const CONFIG = {
  info: { icon: Info, box: 'border-brand-200 bg-brand-50', text: 'text-brand-900', icon_: 'text-brand-600' },
  success: { icon: CheckCircle2, box: 'border-emerald-200 bg-emerald-50', text: 'text-emerald-900', icon_: 'text-emerald-600' },
  warning: { icon: AlertTriangle, box: 'border-gold-200 bg-gold-50', text: 'text-gold-900', icon_: 'text-gold-600' },
  error: { icon: XCircle, box: 'border-crimson-200 bg-crimson-50', text: 'text-crimson-900', icon_: 'text-crimson-600' },
}

export function Alert({ type = 'info', title, children, className, action }) {
  const config = CONFIG[type] ?? CONFIG.info
  const Icon = config.icon

  return (
    <div role="alert" className={cn('flex items-start gap-3 rounded-lg border px-4 py-3', config.box, className)}>
      <Icon className={cn('mt-0.5 h-5 w-5 shrink-0', config.icon_)} aria-hidden="true" />
      <div className={cn('min-w-0 flex-1 text-sm', config.text)}>
        {title ? <p className="font-semibold">{title}</p> : null}
        {children ? <div className={title ? 'mt-0.5' : ''}>{children}</div> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  )
}

export default Alert
