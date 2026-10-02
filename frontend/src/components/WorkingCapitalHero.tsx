import type { Investigation } from '../types'
import { lakh } from '../lib/format'
import { CountUp, Rings } from './fx'

interface Props {
  investigation: Investigation | null
  onViewFindings: () => void
  celebrate: number
}

/** The headline figure in the console rail, styled like the film's ₹12.10 L reveal. */
export function WorkingCapitalHero({ investigation, onViewFindings, celebrate }: Props) {
  const r = investigation?.details?.reconciliation ?? null
  const findingsCount = investigation?.details?.findings.length ?? 0

  let eyebrow = 'Working-capital position'
  let value: number | null = null
  let tone: 'gold' | 'muted' | 'red' = 'muted'
  let qualifier: string

  if (!investigation) {
    qualifier = 'No investigation yet. Attach evidence and run one.'
  } else if (investigation.status === 'error') {
    tone = 'red'
    qualifier = 'The last run did not complete. See the Investigation tab.'
  } else if (!r || !r.can_calculate) {
    qualifier = 'Drawing Power could not be calculated from the evidence supplied yet.'
  } else if (r.gap === null) {
    value = r.calculated_dp ?? 0
    eyebrow = 'Calculated Drawing Power'
    qualifier = 'Nothing in evidence to compare it against yet.'
  } else if (r.gap > 0) {
    value = r.gap
    tone = 'gold'
    eyebrow = 'Potential capacity identified'
    qualifier = r.assumptions_used.length
      ? 'Appears supportable under the facility terms. Built on assumptions; see Investigation.'
      : 'Appears supportable under the facility terms, within the existing sanctioned limit.'
  } else {
    value = 0
    qualifier = 'No evidence of unused capacity in this investigation.'
  }

  return (
    <div className={`hero-card hero-${tone}`}>
      <Rings play={celebrate} />
      <div className="label hero-eyebrow">{eyebrow}</div>
      <div className={`hero-figure num ${tone === 'gold' ? 'gold glow-gold' : tone === 'red' ? 'red' : ''}`} key={celebrate}>
        {value === null ? '—' : <CountUp value={value} format={(n) => lakh(n)} duration={1400} />}
      </div>
      <p className="hero-qual">{qualifier}</p>
      {investigation && (
        <div className="hero-meta">
          <div>
            <span className="num">{investigation.evidence_count_considered}</span>
            <span className="label">evidence</span>
          </div>
          <div>
            <span className="num">{findingsCount}</span>
            <span className="label">findings</span>
          </div>
          <div>
            <span className={`num hero-status st-${investigation.status}`}>{investigation.status.replace('_', ' ')}</span>
            <span className="label">status</span>
          </div>
        </div>
      )}
      {investigation && findingsCount > 0 && (
        <button className="hero-link" onClick={onViewFindings} type="button">
          View supporting findings →
        </button>
      )}
    </div>
  )
}
