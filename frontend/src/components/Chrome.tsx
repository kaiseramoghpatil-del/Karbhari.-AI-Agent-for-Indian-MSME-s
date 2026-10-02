import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { isSoundOn, onSoundChange, setSoundOn, sfx } from '../lib/sound'
import { Icon } from './Icon'

/** Running timecode HH:MM:SS:FF, the film's top-right signature. */
function useTimecode() {
  const [tc, setTc] = useState('')
  useEffect(() => {
    const t0 = performance.now()
    const id = window.setInterval(() => {
      const ms = performance.now() - t0
      const f = Math.floor((ms % 1000) / (1000 / 30))
      const s = Math.floor(ms / 1000)
      const pad = (n: number) => String(n).padStart(2, '0')
      setTc(`${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}:${pad(f)}`)
    }, 50)
    return () => window.clearInterval(id)
  }, [])
  return tc
}

export function SoundToggle() {
  const [on, setOn] = useState(isSoundOn())
  useEffect(() => {
    const off = onSoundChange(setOn)
    return () => {
      off()
    }
  }, [])
  return (
    <button
      type="button"
      className={`sound-toggle${on ? ' on' : ''}`}
      onClick={() => setSoundOn(!on)}
      title={on ? 'Mute interface sounds' : 'Turn interface sounds on'}
      aria-pressed={on}
    >
      <Icon name={on ? 'sound' : 'mute'} size={15} />
      <span>{on ? 'SFX ON' : 'SFX OFF'}</span>
      {on && (
        <span className="eq" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
      )}
    </button>
  )
}

export function Chrome({ section, brandLink = true }: { section: string; brandLink?: boolean }) {
  const tc = useTimecode()
  const brand = (
    <>
      <span className="chrome-brand">KARBHARI</span>
      <span className="chrome-sub">WORKING CAPITAL GUARDIAN</span>
    </>
  )
  return (
    <header className="chrome">
      <div className="chrome-left">
        {brandLink ? (
          <Link to="/" className="chrome-home" onClick={() => sfx.click()}>
            {brand}
          </Link>
        ) : (
          <span className="chrome-home">{brand}</span>
        )}
      </div>
      <div className="chrome-right">
        <span className="chrome-live" aria-hidden="true" />
        <span className="chrome-section">{section}</span>
        <span className="chrome-tc">{tc}</span>
        <SoundToggle />
      </div>
    </header>
  )
}
