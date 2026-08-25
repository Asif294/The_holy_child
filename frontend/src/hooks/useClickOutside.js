import { useEffect } from 'react'

/** Closes dropdowns and menus on an outside click or the Escape key. */
export function useClickOutside(ref, handler, enabled = true) {
  useEffect(() => {
    if (!enabled) return undefined

    function onPointerDown(event) {
      if (ref.current && !ref.current.contains(event.target)) handler(event)
    }
    function onKeyDown(event) {
      if (event.key === 'Escape') handler(event)
    }

    document.addEventListener('mousedown', onPointerDown)
    document.addEventListener('touchstart', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('mousedown', onPointerDown)
      document.removeEventListener('touchstart', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [ref, handler, enabled])
}

export default useClickOutside
