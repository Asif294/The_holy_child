import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Runs an async fetcher and tracks its lifecycle.
 *
 * Deliberately small: this app's screens either load once or reload on an
 * explicit dependency change, which does not justify a data-fetching library.
 */
export function useApi(fetcher, dependencies = [], { immediate = true, initialData = null } = {}) {
  const [data, setData] = useState(initialData)
  const [error, setError] = useState(null)
  const [isLoading, setIsLoading] = useState(immediate)
  const mounted = useRef(true)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  const run = useCallback(async (...args) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await fetcherRef.current(...args)
      if (mounted.current) setData(result)
      return result
    } catch (caught) {
      if (mounted.current) setError(caught)
      throw caught
    } finally {
      if (mounted.current) setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!immediate) return
    run().catch(() => {})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  return { data, error, isLoading, refetch: run, setData }
}

export default useApi
