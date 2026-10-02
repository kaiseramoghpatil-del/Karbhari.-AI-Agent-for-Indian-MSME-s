import type { ReconciliationResult } from '../types'
import { inr, humanize } from '../lib/format'
import { CountUp } from './fx'

/** Drawing Power vs what the bank recognises, drawn like the film's capacity bars. */
export function ReconciliationCard({ reconciliation: r }: { reconciliation: ReconciliationResult }) {
  if (!r.can_calculate) {
    return (
      <div className="panel panel-pad recon">
        <div className="card-head">
          <span className="label">Drawing Power reconciliation</span>
          <span className="chip chip-unresolved">incomplete</span>
        </div>
        <p className="mut">Could not be calculated from the evidence provided. Missing:</p>
        <ul className="missing">
          {r.missing_inputs.map((m, i) => (
            <li key={i}>{m}</li>
          ))}
        </ul>
      </div>
    )
  }

  const calc = r.calculated_dp ?? 0
  const cmp = r.comparison_value ?? 0
  const max = Math.max(calc, cmp, 1)
  const gapPos = (r.gap ?? 0) > 0

  return (
    <div className="panel panel-pad recon">
      <div className="card-head">
        <span className="label">Drawing Power reconciliation</span>
        <span className={`chip ${gapPos ? 'chip-supported' : 'chip-muted'}`}>
          <span className="chip-dot" />
          {gapPos ? 'headroom found' : 'no gap'}
        </span>
      </div>

      <div className="recon-figures">
        <div>
          <div className="label">Calculated DP</div>
          <CountUp value={calc} format={inr} className="num recon-v" />
        </div>
        {r.comparison_basis !== 'none' && (
          <>
            <div>
              <div className="label">{humanize(r.comparison_basis)}</div>
              <CountUp value={cmp} format={inr} className="num recon-v mut" />
            </div>
            <div>
              <div className="label">Gap</div>
              <CountUp value={r.gap ?? 0} format={inr} className={`num recon-v ${gapPos ? 'gold glow-gold' : ''}`} />
            </div>
          </>
        )}
      </div>

      {r.comparison_basis !== 'none' && (
        <div className="cmp-bars">
          <div className="cmp-row">
            <span className="label">Bank today</span>
            <div className="bar bar-lg">
              <i className="bar-red" style={{ width: `${(cmp / max) * 100}%` }} />
            </div>
          </div>
          <div className="cmp-row">
            <span className="label">KARBHARI</span>
            <div className="bar bar-lg">
              <i className="bar-gold" style={{ width: `${(calc / max) * 100}%` }} />
            </div>
          </div>
          {gapPos && cmp > 0 && (
            <div className="cmp-delta num grn">+{(((calc - cmp) / cmp) * 100).toFixed(1)}% headroom</div>
          )}
        </div>
      )}

      {r.assumptions_used.length > 0 && (
        <details className="quotes" open>
          <summary>
            <span className="label">Assumptions used · {r.assumptions_used.length}</span>
          </summary>
          <ul>
            {r.assumptions_used.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}
