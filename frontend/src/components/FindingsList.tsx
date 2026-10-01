import type { Finding } from '../types'

const STATUS_LABEL: Record<Finding['status'], string> = {
  supported: 'Supported',
  unresolved: 'Unresolved',
  ineligible_contradicted: 'Ineligible / Contradicted',
}

function fmtMoney(n: number | null): string {
  if (n === null || n === undefined) return ''
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

export function FindingsList({ findings }: { findings: Finding[] }) {
  if (findings.length === 0) {
    return <div className="empty-state">No findings were produced for this investigation.</div>
  }

  return (
    <div className="findings-list">
      {findings.map((f, i) => (
        <div key={i} className={`finding-card finding-${f.status}`}>
          <div className="finding-head">
            <span className={`status-badge status-badge-${f.status}`}>{STATUS_LABEL[f.status]}</span>
            {f.amount_impact !== null && (
              <span className="finding-amount">{fmtMoney(f.amount_impact)}</span>
            )}
          </div>
          <h4>{f.title}</h4>
          <p>{f.explanation}</p>
          {f.evidence_quotes.length > 0 && (
            <details>
              <summary>Supporting evidence ({f.evidence_quotes.length})</summary>
              <ul className="quote-list">
                {f.evidence_quotes.map((q, qi) => (
                  <li key={qi}>&ldquo;{q}&rdquo;</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      ))}
    </div>
  )
}
