import { useEffect, useRef, useState, type ReactNode } from 'react'

export type Tint = 'gold' | 'red' | 'teal' | 'blue'

/**
 * The film's backdrop as page chrome: drifting dot grid, a tinted radial glow,
 * animated film grain and a vignette. Fixed behind everything; purely visual.
 */
export function Backdrop({ tint = 'gold' }: { tint?: Tint }) {
  return (
    <div className={`backdrop tint-${tint}`} aria-hidden="true">
      <div className="bd-glow" />
      <div className="bd-grid" />
      <div className="bd-grain" />
      <div className="bd-vignette" />
    </div>
  )
}

const reduceMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/** Animates from the previous value to `value` with an ease-out curve. */
export function CountUp({
  value,
  format,
  duration = 1100,
  className,
}: {
  value: number
  format: (n: number) => string
  duration?: number
  className?: string
}) {
  const [shown, setShown] = useState(reduceMotion() ? value : 0)
  const from = useRef(reduceMotion() ? value : 0)

  useEffect(() => {
    if (reduceMotion()) return
    const start = performance.now()
    const a = from.current
    let raf = 0
    const step = (now: number) => {
      const p = Math.min(1, (now - start) / duration)
      const e = 1 - Math.pow(1 - p, 3)
      setShown(a + (value - a) * e)
      if (p < 1) raf = requestAnimationFrame(step)
      else from.current = value
    }
    raf = requestAnimationFrame(step)
    return () => cancelAnimationFrame(raf)
  }, [value, duration])

  return <span className={className}>{format(reduceMotion() ? value : shown)}</span>
}

/** Endless horizontal marquee, like a terminal news strip. */
export function Ticker({ items, slow = false }: { items: ReactNode[]; slow?: boolean }) {
  const row = items.map((it, i) => (
    <span className="ticker-item" key={i}>
      {it}
    </span>
  ))
  return (
    <div className={`ticker${slow ? ' ticker-slow' : ''}`} aria-hidden="true">
      <div className="ticker-track">
        {row}
        {row}
      </div>
    </div>
  )
}

/** Wraps children in a staggered rise-in. `i` sets the stagger order. */
export function Reveal({ i = 0, children, className = '' }: { i?: number; children: ReactNode; className?: string }) {
  return (
    <div className={`reveal ${className}`} style={{ ['--i' as string]: i }}>
      {children}
    </div>
  )
}

/** Expanding gold rings, as in the film's discovery moment. */
export function Rings({ play }: { play: number }) {
  if (!play) return null
  return (
    <span className="rings" key={play} aria-hidden="true">
      <span />
      <span />
      <span />
    </span>
  )
}

/** Tiny decorative sparkline (deterministic from a seed). */
export function Sparkline({ seed, color = 'var(--gold)', width = 120, height = 32 }: { seed: string; color?: string; width?: number; height?: number }) {
  let h = 0
  for (const ch of seed) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  const pts: number[] = []
  let v = 0.5
  for (let i = 0; i < 18; i++) {
    h = (h * 1103515245 + 12345) >>> 0
    v = Math.min(0.95, Math.max(0.08, v + ((h % 1000) / 1000 - 0.45) * 0.28))
    pts.push(v)
  }
  const d = pts.map((p, i) => `${i ? 'L' : 'M'}${(i / (pts.length - 1)) * width},${height - p * height}`).join(' ')
  return (
    <svg className="sparkline" width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <path d={`${d} L${width},${height} L0,${height} Z`} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
    </svg>
  )
}
