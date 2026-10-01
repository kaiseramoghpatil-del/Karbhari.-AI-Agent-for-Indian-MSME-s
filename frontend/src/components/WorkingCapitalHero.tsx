import { DottedGlowBackground } from './DottedGlowBackground'
import type { Investigation } from '../types'

function fmtLakh(n: number): string {
  const abs = Math.abs(n)
  const sign = n < 0 ? '−' : ''
  if (abs >= 1_00_00_000) return `${sign}₹${(abs / 1_00_00_000).toFixed(2)}Cr`
  if (abs >= 1_00_000) return `${sign}₹${(abs / 1_00_000).toFixed(2)}L`
  if (abs >= 1_000) return `${sign}₹${(abs / 1_000).toFixed(1)}K`
  return `${sign}₹${abs.toFixed(0)}`
}

interface Props {
  investigation: Investigation | null
  onViewFindings: () => void
}

export function WorkingCapitalHero({ investigation, onViewFindings }: Props) {
  const reconciliation = investigation?.details?.reconciliation ?? null
  const findingsCount = investigation?.details?.findings.length ?? 0

  let eyebrow = 'WORKING-CAPITAL POSITION'
  let headline: string
  let headlineTone: 'gold' | 'muted' = 'muted'
  let qualifier: string

  if (!investigation) {
    headline = '—'
    qualifier = 'No investigation has been run on this case yet.'
  } else if (investigation.status === 'error') {
    headline = '—'
    qualifier = 'The last investigation run did not complete. See the Investigation tab.'
  } else if (!reconciliation || !reconciliation.can_calculate) {
    headline = '—'
    qualifier = 'Drawing Power could not be independently calculated from the evidence supplied.'
  } else if (reconciliation.gap === null) {
    headline = fmtLakh(reconciliation.calculated_dp ?? 0)
    headlineTone = 'muted'
    qualifier = 'Calculated, but nothing in evidence to compare it against yet.'
  } else if (reconciliation.gap > 0) {
    headline = fmtLakh(reconciliation.gap)
    headlineTone = 'gold'
    eyebrow = 'POTENTIAL WORKING-CAPITAL CAPACITY IDENTIFIED'
    qualifier = reconciliation.assumptions_used.length > 0
      ? 'Appears supportable under the supplied facility terms — built on assumptions; see Investigation.'
      : 'Appears supportable under the supplied facility terms, within the existing sanctioned limit.'
  } else {
    headline = '₹0'
    headlineTone = 'muted'
    eyebrow = 'WORKING-CAPITAL POSITION'
    qualifier = 'No evidence of unused capacity was found in this investigation.'
  }

  return (
    <div className="hero">
      <DottedGlowBackground className="hero-canvas" />
      <div className="hero-content">
        <div className="hero-eyebrow">{eyebrow}</div>
        <div className={`hero-figure tabular-nums hero-figure-${headlineTone}`}>{headline}</div>
        <p className="hero-qualifier">{qualifier}</p>
        <div className="hero-meta">
          {investigation && (
            <>
              <span>{investigation.evidence_count_considered} evidence item(s) considered</span>
              <span className="hero-meta-dot">·</span>
              <span>{findingsCount} finding(s)</span>
              <span className="hero-meta-dot">·</span>
              <span className="hero-status">{investigation.status.replace('_', ' ')}</span>
            </>
          )}
        </div>
        {investigation && findingsCount > 0 && (
          <button className="hero-link" onClick={onViewFindings} type="button">
            View supporting findings ↓
          </button>
        )}
      </div>
    </div>
  )
}
