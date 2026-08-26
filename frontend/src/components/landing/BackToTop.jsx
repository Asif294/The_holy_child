import { useEffect, useState } from 'react'
import { ArrowUp } from 'lucide-react'

import cn from '@/utils/cn'

//: How far down the page the button becomes useful. Roughly one screen — above
//: that the header is still in reach and a floating button is just clutter.
const REVEAL_AFTER = 400

/**
 * A "back to top" button that fades in once the visitor has scrolled.
 *
 * The public site is one long page, so the way back to the top matters. It is
 * hidden until scrolling makes it worth showing, and it animates only for
 * visitors who have not asked their system for reduced motion.
 */
export function BackToTop() {
  const [isVisible, setVisible] = useState(false)

  useEffect(() => {
    function onScroll() {
      setVisible(window.scrollY > REVEAL_AFTER)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  function scrollToTop() {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    window.scrollTo({ top: 0, behavior: reducedMotion ? 'auto' : 'smooth' })
  }

  return (
    <button
      type="button"
      onClick={scrollToTop}
      aria-label="Back to top"
      // Hidden from everything, not just from view: an invisible button is not
      // one a keyboard or a screen reader should still find.
      aria-hidden={!isVisible}
      tabIndex={isVisible ? 0 : -1}
      className={cn(
        'fixed bottom-6 right-6 z-40 grid h-11 w-11 place-items-center rounded-full',
        'bg-gold-500 text-brand-950 shadow-lg shadow-brand-950/25 transition-all duration-200',
        'hover:bg-gold-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
        'focus-visible:outline-gold-500',
        isVisible ? 'translate-y-0 opacity-100' : 'pointer-events-none translate-y-3 opacity-0',
      )}
    >
      <ArrowUp className="h-5 w-5" aria-hidden="true" />
    </button>
  )
}

export default BackToTop
