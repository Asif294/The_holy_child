import api from './api'

/**
 * Builds the standard REST calls for a resource.
 *
 * Every module in this app talks to a DRF ModelViewSet with identical routes,
 * so each service is a one-line factory call plus whatever is genuinely
 * specific to that resource.
 *
 * There is deliberately no `PUT`. Every edit screen here sends the fields it
 * actually changed, and `PUT` means "replace the record with this" — anything
 * the form did not send would be blanked, which for a partly-filled student or
 * teacher record is data loss rather than an edit. `patch` is the only update.
 */
export function createCrudService(resource) {
  const base = `/${resource}/`

  return {
    base,
    async list(params = {}) {
      const { data } = await api.get(base, { params })
      return data
    },
    /** Convenience for selects: returns a plain array, never a page object. */
    async all(params = {}) {
      const { data } = await api.get(base, { params: { ...params, paginated: false } })
      return Array.isArray(data) ? data : (data.results ?? [])
    },
    async retrieve(id) {
      const { data } = await api.get(`${base}${id}/`)
      return data
    },
    async create(payload) {
      const { data } = await api.post(base, payload)
      return data
    },
    /** The only update: a partial one, so untouched fields keep their values. */
    async patch(id, payload) {
      const { data } = await api.patch(`${base}${id}/`, payload)
      return data
    },
    async remove(id) {
      const { data } = await api.delete(`${base}${id}/`)
      return data
    },
  }
}

export default createCrudService
