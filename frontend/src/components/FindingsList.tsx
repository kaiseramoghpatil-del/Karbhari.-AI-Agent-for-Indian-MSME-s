import type { Finding } from '../types'
import { inr } from '../lib/format'
import { Reveal } from './fx'

const STATUS_LABEL: Record<Finding['status'], string> = {
  supported: 'Supported',
  unresolved: 'Unresolved',
  ineligible_contradicted: 'Contradicted',
}

/** Closing tile: how the findings break down, plus the at-stake total. */
function FindingsSummary({ findings }: { findings: Finding[] }) {
  const by = (s: Finding['status']) => findings.filter((f) => f.status === s).length
  const rows: [string, number, string][] = [
    ['Supported', by('supported'), 'var(--grn)'],
    ['Unresolved', by('unresolved'), 'var(--amber)'],
    ['Contradicted', by('ineligible_contradicted'), 'var(--red)'],
  ]
  return (
    <div className="panel finding-summary">
      <div className="label">Findings at a glance</div>
      <div className="fs-total num gold glow-gold">
        {by('supported')}
        <span className="fs-of">/{findings.length}</span>
      </div>
      <div className="label fs-sub">fully supported by evidence</div>
      <div className="fs-rows">
        {rows.map(([l, n, c]) => (
          <div className="fs-row" key={l}>
            <span>{l}</span>
            <div className="bar">
              <i style={{ width: `${(n / Math.max(1, findings.length)) * 100}%`, background: c, boxShadow: `0 0 12px ${c}` }} />
            </div>
            <span className="num">{n}</span>
          </div>
        ))}
      </div>
      <p className="fs-note">Every amount is computed by KARBHARI&apos;s tested engines, never by the language model.</p>
    </div>
  )
}

export function FindingsList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) {
    return <div className="empty panel panel-pad">No findings were produced for this investigation.</div>
  }

  return (
    <div className="findings-grid">
      {findings.map((f, i) => (
        <Reveal i={i} key={i}>
          <article className={`finding panel finding-${f.status}`}>
            <span className="finding-edge" />
            <div className="finding-head">
              <span className={`chip chip-${f.status}`}>
                <span className="chip-dot" />
                {STATUS_LABEL[f.status]}
              </span>
              {f.amount_impact !== null && <span className="finding-amount num">{inr(f.amount_impact)}</span>}
            </div>
            <h4 className="finding-title">{f.title}</h4>
            <p className="finding-body">{f.explanation}</p>
            {f.evidence_quotes.length > 0 && (
              <details className="quotes">
                <summary>
                  <span className="label">Supporting evidence · {f.evidence_quotes.length}</span>
                </summary>
                <ul>
                  {f.evidence_quotes.map((q, qi) => (
                    <li key={qi}>“{q}”</li>
                  ))}
                </ul>
              </details>
            )}
          </article>
        </Reveal>
      ))}
      <Reveal i={findings.length}>
        <FindingsSummary findings={findings} />
      </Reveal>
    </div>
  )
}
