import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { ChevronLeft, ChevronRight, Pause, Play, Sparkles } from 'lucide-react'

import cn from '@/utils/cn'
import useSchool from '@/hooks/useSchool'
import { formatNumber } from '@/utils/formatters'

const INTERVAL_MS = 6000

/**
 * The rotating banner at the top of the landing page.
 *
 * Slides come from the API, so an administrator adds and reorders them without
 * a deploy. When there are none — a fresh install, or a failed request — the
 * built-in slide below renders instead: the page should look finished before
 * anyone has uploaded anything.
 *
 * Rotation pauses on hover, on keyboard focus and whenever the tab is hidden,
 * and stops for good once a visitor uses the arrows: someone reading a slide
 * should not have it pulled away from them.
 */
export function HeroSlider({ slides = [], stats }) {
  const { school } = useSchool()

  const items = useMemo(() => (slides.length ? slides : [null]), [slides])
  const [index, setIndex] = useState(0)
  const [isPaused, setPaused] = useState(false)
  const [isStopped, setStopped] = useState(false)
  const timer = useRef(null)

  const count = items.length
  const goTo = useCallback((next) => setIndex(((next % count) + count) % count), [count])
  const next = useCallback(() => goTo(index + 1), [goTo, index])
  const previous = useCallback(() => goTo(index - 1), [goTo, index])

  // Stepping through by hand is a request to stop the carousel, not to restart it.
  const step = useCallback(
    (direction) => {
      setStopped(true)
      goTo(index + direction)
    },
    [goTo, index],
  )

  useEffect(() => {
    if (count < 2 || isPaused || isStopped) return undefined
    timer.current = setTimeout(next, INTERVAL_MS)
    return () => clearTimeout(timer.current)
  }, [count, index, isPaused, isStopped, next])

  // A carousel advancing in a background tab is wasted motion.
  useEffect(() => {
    function onVisibility() {
      setPaused(document.hidden)
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [])

  function onKeyDown(event) {
    if (event.key === 'ArrowRight') {
      event.preventDefault()
      step(1)
    } else if (event.key === 'ArrowLeft') {
      event.preventDefault()
      step(-1)
    }
  }

  const figures = [
    { label: 'Students', value: formatNumber(stats?.students ?? 0) },
    { label: 'Teachers', value: formatNumber(stats?.teachers ?? 0) },
    { label: 'Classes', value: formatNumber(stats?.classes ?? 0) },
  ]

  return (
    <section id="home" className="relative bg-brand-950 pt-16">
      <div
        className="group relative isolate overflow-hidden"
        onMouseEnter={() => setPaused(true)}
        onMouseLeave={() => setPaused(false)}
        onFocus={() => setPaused(true)}
        onBlur={() => setPaused(false)}
        onKeyDown={onKeyDown}
        role="region"
        aria-roledescription="carousel"
        aria-label="School highlights"
        tabIndex={0}
      >
        <div className="relative h-[30rem] sm:h-[34rem] lg:h-[38rem]">
          {items.map((slide, position) => (
            <Slide
              key={slide?.id ?? 'fallback'}
              slide={slide}
              school={school}
              isCurrent={position === index}
              position={position}
              total={count}
            />
          ))}

          {/* Copy overlay — shared by every slide so the layout never jumps. */}
          <div className="pointer-events-none absolute inset-0 flex items-end">
            <div className="mx-auto w-full max-w-7xl px-4 pb-16 sm:px-6 lg:px-8 lg:pb-24">
              <div className="pointer-events-auto max-w-2xl">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold text-gold-300 backdrop-blur">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                  {items[index]?.caption || `Established ${school.established} · ${school.address}`}
                </span>

                <h1 className="mt-5 text-4xl font-extrabold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl">
                  {items[index]?.title || school.name_en}
                </h1>

                <p className="mt-4 max-w-xl text-lg leading-relaxed text-brand-100">
                  {items[index]?.subtitle ||
                    `${school.grade_range} — a disciplined, caring education for the children of ${
                      (school.address || '').split(',')[0] || 'our community'
                    }.`}
                </p>

                <p className="font-bangla mt-3 text-base text-brand-200" lang="bn">
                  {school.name_bn}
                </p>

                {items[index]?.link_url && items[index]?.link_label ? (
                  <a
                    href={items[index].link_url}
                    className="mt-7 inline-flex h-11 items-center rounded-lg bg-gold-500 px-5 text-base font-semibold text-brand-950 transition-colors hover:bg-gold-400"
                  >
                    {items[index].link_label}
                  </a>
                ) : null}

                <dl className="mt-9 grid max-w-md grid-cols-3 gap-6 border-t border-white/15 pt-6">
                  {figures.map((figure) => (
                    <div key={figure.label}>
                      <dt className="text-xs font-medium uppercase tracking-wide text-brand-200">
                        {figure.label}
                      </dt>
                      <dd className="mt-1 text-2xl font-bold tracking-tight text-white">{figure.value}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            </div>
          </div>

          {count > 1 ? (
            <>
              <SliderButton side="left" onClick={() => step(-1)} label="Previous slide">
                <ChevronLeft className="h-5 w-5" />
              </SliderButton>
              <SliderButton side="right" onClick={() => step(1)} label="Next slide">
                <ChevronRight className="h-5 w-5" />
              </SliderButton>

              <div className="absolute bottom-5 right-4 flex items-center gap-3 sm:right-6 lg:right-8">
                <button
                  type="button"
                  onClick={() => setStopped((stopped) => !stopped)}
                  className="rounded-full border border-white/25 bg-black/30 p-2 text-white backdrop-blur transition-colors hover:bg-black/50"
                  aria-label={isStopped ? 'Resume the slideshow' : 'Pause the slideshow'}
                >
                  {isStopped ? <Play className="h-3.5 w-3.5" /> : <Pause className="h-3.5 w-3.5" />}
                </button>

                <div className="flex items-center gap-2" role="tablist" aria-label="Choose a slide">
                  {items.map((slide, position) => (
                    <button
                      key={slide?.id ?? position}
                      type="button"
                      role="tab"
                      aria-selected={position === index}
                      aria-label={`Slide ${position + 1} of ${count}`}
                      onClick={() => {
                        setStopped(true)
                        goTo(position)
                      }}
                      className={cn(
                        'h-2 rounded-full transition-all',
                        position === index ? 'w-7 bg-gold-400' : 'w-2 bg-white/45 hover:bg-white/70',
                      )}
                    />
                  ))}
                </div>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </section>
  )
}

/** One image layer. Every slide stays mounted so the cross-fade has something to fade to. */
function Slide({ slide, school, isCurrent, position, total }) {
  return (
    <div
      className={cn(
        'absolute inset-0 transition-opacity duration-700 ease-out',
        isCurrent ? 'opacity-100' : 'opacity-0',
      )}
      role="group"
      aria-roledescription="slide"
      aria-label={`Slide ${position + 1} of ${total}`}
      aria-hidden={!isCurrent}
    >
      {slide?.image_url ? (
        <img
          src={slide.image_url}
          alt={slide.alt_text || slide.title || school.name_en}
          className="h-full w-full object-cover"
          loading={position === 0 ? 'eager' : 'lazy'}
        />
      ) : (
        <FallbackBackdrop />
      )}
      {/* Dark wash so white type stays legible over any photograph. */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-brand-950 via-brand-950/70 to-brand-950/25"
        aria-hidden="true"
      />
    </div>
  )
}

/** What the hero looks like before anyone has uploaded a photograph. */
function FallbackBackdrop() {
  return (
    <div className="h-full w-full bg-gradient-to-br from-brand-800 via-brand-900 to-brand-950">
      <div
        className="h-full w-full opacity-[0.12]"
        aria-hidden="true"
        style={{
          backgroundImage:
            'radial-gradient(circle at 18% 22%, white 1.5px, transparent 1.5px), radial-gradient(circle at 72% 62%, white 1.5px, transparent 1.5px)',
          backgroundSize: '56px 56px, 76px 76px',
        }}
      />
    </div>
  )
}

function SliderButton({ side, onClick, label, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className={cn(
        'absolute top-1/2 z-10 -translate-y-1/2 rounded-full border border-white/25 bg-black/30 p-3 text-white backdrop-blur',
        'transition-all hover:bg-black/60 focus-visible:opacity-100',
        'opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 sm:opacity-70',
        side === 'left' ? 'left-3 sm:left-5' : 'right-3 sm:right-5',
      )}
    >
      {children}
    </button>
  )
}

export default HeroSlider
