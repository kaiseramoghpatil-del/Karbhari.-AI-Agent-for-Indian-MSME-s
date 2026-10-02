/**
 * Synthesized UI sound design (Web Audio, no audio files), in the same spirit as
 * the explainer film's score: soft clicks, filtered-noise whooshes, a two-note
 * "verified" chime and a low impact when a result lands. Everything is quiet by
 * default and can be muted from the top bar; the choice persists per browser.
 */

const STORAGE_KEY = 'karbhari:sound'

let ctx: AudioContext | null = null
let master: GainNode | null = null
let noiseBuf: AudioBuffer | null = null
let enabled = readPref()
const listeners = new Set<(on: boolean) => void>()

function readPref(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) !== 'off'
  } catch {
    return true
  }
}

export function isSoundOn() {
  return enabled
}

export function setSoundOn(on: boolean) {
  enabled = on
  try {
    localStorage.setItem(STORAGE_KEY, on ? 'on' : 'off')
  } catch {
    /* private mode: preference just won't persist */
  }
  listeners.forEach((l) => l(on))
  if (on) sfx.chime()
}

export function onSoundChange(fn: (on: boolean) => void) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

function ac(): AudioContext | null {
  if (!enabled) return null
  try {
    if (!ctx) {
      ctx = new AudioContext()
      master = ctx.createGain()
      master.gain.value = 0.32
      master.connect(ctx.destination)
    }
    if (ctx.state === 'suspended') void ctx.resume()
    return ctx
  } catch {
    return null
  }
}

function noise(c: AudioContext): AudioBuffer {
  if (!noiseBuf) {
    noiseBuf = c.createBuffer(1, c.sampleRate, c.sampleRate)
    const d = noiseBuf.getChannelData(0)
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1
  }
  return noiseBuf
}

function tone(freq: number, dur: number, gain: number, type: OscillatorType = 'sine', glideTo?: number, delay = 0) {
  const c = ac()
  if (!c || !master) return
  const t = c.currentTime + delay
  const o = c.createOscillator()
  const g = c.createGain()
  o.type = type
  o.frequency.setValueAtTime(freq, t)
  if (glideTo) o.frequency.exponentialRampToValueAtTime(glideTo, t + dur)
  g.gain.setValueAtTime(0.0001, t)
  g.gain.exponentialRampToValueAtTime(gain, t + 0.005)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  o.connect(g).connect(master)
  o.start(t)
  o.stop(t + dur + 0.02)
}

function hiss(dur: number, gain: number, filter: BiquadFilterType, from: number, to?: number, q = 1, delay = 0) {
  const c = ac()
  if (!c || !master) return
  const t = c.currentTime + delay
  const src = c.createBufferSource()
  src.buffer = noise(c)
  const f = c.createBiquadFilter()
  f.type = filter
  f.Q.value = q
  f.frequency.setValueAtTime(from, t)
  if (to) f.frequency.exponentialRampToValueAtTime(to, t + dur)
  const g = c.createGain()
  g.gain.setValueAtTime(0.0001, t)
  g.gain.exponentialRampToValueAtTime(gain, t + dur * 0.3)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  src.connect(f).connect(g).connect(master)
  src.start(t)
  src.stop(t + dur + 0.02)
}

export const sfx = {
  /** Button press. */
  click() {
    tone(1650, 0.05, 0.12)
    hiss(0.03, 0.08, 'highpass', 3000)
  },
  /** Very small tick for hovers and counters. */
  tick() {
    tone(2600 + Math.random() * 600, 0.02, 0.03)
  },
  /** Tab / view change. */
  whoosh() {
    hiss(0.34, 0.16, 'bandpass', 320, 3200, 1.4)
  },
  /** Something was verified or saved. */
  chime() {
    tone(1174.7, 0.5, 0.07)
    tone(1568, 0.55, 0.06, 'sine', undefined, 0.08)
  },
  /** Headline result lands. */
  impact() {
    tone(92, 0.9, 0.5, 'sine', 32)
    hiss(0.12, 0.25, 'lowpass', 1800)
    for (let i = 0; i < 7; i++) tone(2400 + Math.random() * 3200, 0.5, 0.012, 'sine', undefined, 0.05 + i * 0.06)
  },
  /** Text slam / emphasis. */
  slam() {
    tone(115, 0.22, 0.28, 'sine', 45)
    hiss(0.05, 0.12, 'lowpass', 2200)
  },
  /** Problem / failure. */
  buzz() {
    tone(110, 0.2, 0.06, 'sawtooth')
    tone(116.5, 0.2, 0.05, 'sawtooth')
  },
  /** Paper landing (upload). */
  paper() {
    hiss(0.22, 0.12, 'lowpass', 3800, 1200)
  },
  /** Soft scanner loop for long-running work. Returns a stop function. */
  scanLoop(): () => void {
    hiss(0.6, 0.06, 'bandpass', 600, 2400, 2)
    const id = window.setInterval(() => {
      sfx.tick()
      if (Math.random() < 0.18) hiss(0.5, 0.05, 'bandpass', 500 + Math.random() * 400, 2600, 2)
    }, 140)
    return () => window.clearInterval(id)
  },
}
