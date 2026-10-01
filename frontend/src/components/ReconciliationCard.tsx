import type { ReconciliationResult } from '../types'

function fmtMoney(n: number | null): string {
  if (n === null || n === undefined) return '—'
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

export function ReconciliationCard({ reconciliation }: { reconciliation: ReconciliationResult }) {
  if (!reconciliation.can_calculate) {
    return (
      <div className="card reconciliation-card">
        <h3>Drawing Power reconciliation</h3>
        <p className="muted">Could not be calculated from the evidence provided.</p>
        {reconciliation.missing_inputs.length > 0 && (
          <ul className="quote-list">
            {reconciliation.missing_inputs.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  return (
    <div className="card reconciliation-card">
      <h3>Drawing Power reconciliation</h3>
      <div className="dp-figures">
        <div>
          <span className="muted">Calculated DP</span>
          <div className="dp-value">{fmtMoney(reconciliation.calculated_dp)}</div>
        </div>
        {reconciliation.comparison_basis !== 'none' && (
          <>
            <div>
              <span className="muted">{reconciliation.comparison_basis.replace('_', ' ')}</span>
              <div className="dp-value">{fmtMoney(reconciliation.comparison_value)}</div>
            </div>
            <div>
              <span className="muted">Gap</span>
              <div className={`dp-value ${(reconciliation.gap ?? 0) > 0 ? 'dp-gap-positive' : ''}`}>
                {fmtMoney(reconciliation.gap)}
              </div>
            </div>
          </>
        )}
      </div>
      {reconciliation.assumptions_used.length > 0 && (
        <details>
          <summary>Assumptions used in this calculation ({reconciliation.assumptions_used.length})</summary>
          <ul className="quote-list">
            {reconciliation.assumptions_used.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
