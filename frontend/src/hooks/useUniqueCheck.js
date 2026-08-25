import { useCallback, useEffect, useRef } from 'react'

/**
 * A debounced "is this code still free?" check for a unique field.
 *
 * The save is what actually enforces uniqueness — the server always re-checks,
 * and two clerks typing the same ID at the same moment can only be separated
 * there. This exists so somebody who types over a generated ID learns it is
 * taken while they are still looking at the field, instead of after pressing
 * the button.
 *
 * `check(params)` is the service call; it should resolve to `{ field: message }`
 * for whatever clashes, and `{}` when nothing does.
 */
export function useUniqueCheck(check, setErrors, delay = 400) {
  const timers = useRef({})
  const latest = useRef({})

  // A check still in flight when the form closes must not land on the next one.
  useEffect(() => {
    const pending = timers.current
    return () => Object.values(pending).forEach(clearTimeout)
  }, [])

  return useCallback(
    (name, value, params = {}) => {
      clearTimeout(timers.current[name])
      // An empty field is not a clash — it means "issue me the next one".
      if (!check || !value) return

      timers.current[name] = setTimeout(async () => {
        const ticket = (latest.current[name] ?? 0) + 1
        latest.current[name] = ticket
        try {
          const clashes = await check({ [name]: value, ...params })
          // A slow answer about an old value must not overwrite a newer one.
          if (latest.current[name] !== ticket) return
          setErrors((current) => ({ ...current, [name]: clashes?.[name] }))
        } catch {
          // A check that could not run is not a validation failure — say
          // nothing and let the save be the judge.
        }
      }, delay)
    },
    [check, setErrors, delay],
  )
}

export default useUniqueCheck
