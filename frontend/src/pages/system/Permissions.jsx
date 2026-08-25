import { useMemo, useState } from 'react'
import { KeyRound, Search } from 'lucide-react'

import Alert from '@/components/ui/Alert'
import Badge from '@/components/ui/Badge'
import Card, { CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Input from '@/components/ui/Input'
import { LoadingState } from '@/components/ui/Spinner'
import PageHeader from '@/components/common/PageHeader'
import useApi from '@/hooks/useApi'
import useDocumentTitle from '@/hooks/useDocumentTitle'
import { permissionService } from '@/services'

export function Permissions() {
  useDocumentTitle('Permissions')

  const { data: groups, error, isLoading } = useApi(() => permissionService.grouped(), [], { initialData: [] })
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const term = query.trim().toLowerCase()
    if (!term) return groups

    return groups
      .map((group) => ({
        ...group,
        modules: group.modules
          .map((module) => ({
            ...module,
            permissions: module.permissions.filter(
              (permission) =>
                permission.code.toLowerCase().includes(term) ||
                permission.name.toLowerCase().includes(term) ||
                module.label.toLowerCase().includes(term),
            ),
          }))
          .filter((module) => module.permissions.length > 0),
      }))
      .filter((group) => group.modules.length > 0)
  }, [groups, query])

  const total = useMemo(
    () => groups.reduce((sum, group) => sum + group.modules.reduce((n, m) => n + m.permissions.length, 0), 0),
    [groups],
  )

  return (
    <div>
      <PageHeader
        title="Permissions"
        description="The full catalogue of capabilities the platform understands. Permissions are defined in code and seeded — roles decide who holds them."
      />

      <Alert type="info" className="mb-5">
        This catalogue is read-only. To grant a capability, add it to a role under{' '}
        <span className="font-semibold">Roles</span>.
      </Alert>

      <div className="mb-5 flex flex-wrap items-center gap-3">
        <Input
          containerClassName="w-full sm:max-w-sm"
          placeholder="Search by code, name or module…"
          leftIcon={<Search className="h-4 w-4" />}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="Search permissions"
        />
        <Badge tone="brand">{total} permissions</Badge>
      </div>

      {error ? (
        <Alert type="error" title="Could not load permissions">
          {error.message}
        </Alert>
      ) : isLoading ? (
        <LoadingState />
      ) : filtered.length === 0 ? (
        <Card>
          <EmptyState icon={KeyRound} title="No permissions match" description="Try a different search term." />
        </Card>
      ) : (
        <div className="space-y-5">
          {filtered.map((group) => (
            <Card key={group.group}>
              <CardHeader
                title={group.group}
                description={`${group.modules.length} module${group.modules.length === 1 ? '' : 's'}`}
              />
              <div className="divide-y divide-slate-100">
                {group.modules.map((module) => (
                  <div key={module.module} className="flex flex-wrap items-start gap-x-6 gap-y-2 px-5 py-3.5">
                    <div className="w-44 shrink-0">
                      <p className="text-sm font-medium text-slate-800">{module.label}</p>
                      <p className="font-mono text-xs text-slate-400">{module.module}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {module.permissions.map((permission) => (
                        <span
                          key={permission.code}
                          title={permission.name}
                          className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700 ring-1 ring-inset ring-slate-200"
                        >
                          {permission.code}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default Permissions
