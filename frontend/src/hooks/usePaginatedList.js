import { useCallback, useEffect, useMemo, useState } from 'react'

import { DEFAULT_PAGE_SIZE } from '@/utils/constants'
import useDebounce from './useDebounce'

/**
 * Page, search and filter state for a DRF-backed list endpoint.
 *
 * Every list screen in the app needs the same five things — rows, a page,
 * a search box, filters and a reload — so they all share this hook rather than
 * each re-implementing the wiring.
 */
export function usePaginatedList(service, { pageSize = DEFAULT_PAGE_SIZE, initialFilters = {}, ordering } = {}) {
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState(initialFilters)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  const debouncedSearch = useDebounce(search, 350)

  const activeFilters = useMemo(
    () => Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== '' && value != null)),
    [filters],
  )

  const load = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await service.list({
        page,
        page_size: pageSize,
        ...(debouncedSearch ? { search: debouncedSearch } : {}),
        ...(ordering ? { ordering } : {}),
        ...activeFilters,
      })
      const results = Array.isArray(response) ? response : (response.results ?? [])
      setItems(results)
      setCount(Array.isArray(response) ? results.length : (response.count ?? results.length))
      setTotalPages(Array.isArray(response) ? 1 : (response.total_pages ?? 1))
    } catch (caught) {
      setError(caught)
      setItems([])
    } finally {
      setIsLoading(false)
    }
  }, [service, page, pageSize, debouncedSearch, ordering, activeFilters])

  useEffect(() => {
    load()
  }, [load])

  // Any change to the query resets to the first page — otherwise a filtered
  // result set can land the user on a page that no longer exists.
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, activeFilters])

  const setFilter = useCallback((key, value) => {
    setFilters((current) => ({ ...current, [key]: value }))
  }, [])

  const resetFilters = useCallback(() => {
    setFilters(initialFilters)
    setSearch('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    items,
    count,
    page,
    setPage,
    totalPages,
    pageSize,
    search,
    setSearch,
    filters,
    setFilter,
    setFilters,
    resetFilters,
    isLoading,
    error,
    reload: load,
  }
}

export default usePaginatedList
