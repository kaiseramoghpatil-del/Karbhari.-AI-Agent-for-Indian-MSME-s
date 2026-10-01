import { useEffect, useRef } from 'react'

/**
 * Hand-rolled dotted-glow backdrop: a sparse grid of dots, each pulsing its
 * own glow independently and slowly. Adapted from the visual language of
 * Aceternity's "Dotted Glow Background" but recolored (muted ink dots,
 * restrained gold glow -- never the default bright AI-blue) and
 * reimplemented directly on canvas rather than pulling in their
 * shadcn/framer-motion-based package, which would drag a whole component
 * ecosystem into the app for one texture.
 *
 * Deliberately used in exactly one place in the product (the working-capital
 * hero) -- this is a mood-setting backdrop, not a page-wide effect.
 */

interface DottedGlowBackgroundProps {
  dotColor?: string
  glowColor?: string
  gap?: number
  dotRadius?: number
  baseAlpha?: number
  peakAlpha?: number
  className?: string
}

export function DottedGlowBackground({
  dotColor = '#9fb0c2',
  glowColor = '#c9a13b',
  gap = 12,
  dotRadius = 1.1,
  baseAlpha = 0.18,
  peakAlpha = 0.55,
  className,
}: DottedGlowBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    let width = 0
    let height = 0
    let dpr = Math.min(window.devicePixelRatio || 1, 2)
    let dots: { x: number; y: number; phase: number; speed: number }[] = []
    let frame = 0

    function resize() {
      const parent = canvas!.parentElement
      if (!parent) return
      width = parent.clientWidth
      height = parent.clientHeight
      canvas!.width = width * dpr
      canvas!.height = height * dpr
      canvas!.style.width = `${width}px`
      canvas!.style.height = `${height}px`
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0)

      dots = []
      for (let x = gap / 2; x < width; x += gap) {
        for (let y = gap / 2; y < height; y += gap) {
          dots.push({
            x,
            y,
            phase: Math.random() * Math.PI * 2,
            speed: 0.15 + Math.random() * 0.35, // slow, restrained -- not a flashy pulse
          })
        }
      }
    }

    function draw() {
      ctx!.clearRect(0, 0, width, height)
      for (const d of dots) {
        const t = reduceMotion ? 0 : Math.sin(d.phase + frame * 0.016 * d.speed)
        const alpha = baseAlpha + ((t + 1) / 2) * (peakAlpha - baseAlpha)

        if (t > 0.6 && !reduceMotion) {
          // soft glow only near the peak of each dot's own cycle
          ctx!.beginPath()
          ctx!.fillStyle = glowColor
          ctx!.globalAlpha = (t - 0.6) * 0.5
          ctx!.filter = 'blur(3px)'
          ctx!.arc(d.x, d.y, dotRadius * 2.4, 0, Math.PI * 2)
          ctx!.fill()
          ctx!.filter = 'none'
        }

        ctx!.beginPath()
        ctx!.fillStyle = dotColor
        ctx!.globalAlpha = alpha
        ctx!.arc(d.x, d.y, dotRadius, 0, Math.PI * 2)
        ctx!.fill()
      }
      ctx!.globalAlpha = 1
    }

    let raf = 0
    function loop() {
      frame++
      draw()
      if (!reduceMotion) raf = requestAnimationFrame(loop)
    }

    resize()
    draw()
    if (!reduceMotion) raf = requestAnimationFrame(loop)

    const ro = new ResizeObserver(resize)
    ro.observe(canvas.parentElement!)

    return () => {
      cancelAnimationFrame(raf)
      ro.disconnect()
    }
  }, [dotColor, glowColor, gap, dotRadius, baseAlpha, peakAlpha])

  return (
    <canvas
      ref={canvasRef}
      className={className}
      style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}
      aria-hidden="true"
    />
  )
}
