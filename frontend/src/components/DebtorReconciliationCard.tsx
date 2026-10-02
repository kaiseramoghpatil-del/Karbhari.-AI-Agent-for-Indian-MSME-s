import type { DebtorReconciliation, ConsistencyResult } from '../types'
import { inr, humanize } from '../lib/format'
import { CountUp, Reveal } from './fx'

interface Props {
  debtorReconciliation: DebtorReconciliation | null
  consistency: ConsistencyResult | null
}

/** Eligible vs ineligible share of the debtor book as a ring. */
function Donut({ eligible, total }: { eligible: number; total: number }) {
  const r = 46
  const c = 2 * Math.PI * r
  const share = total > 0 ? eligible / total : 0
  return (
    <svg className="donut" viewBox="0 0 120 120" aria-hidden="true">
      <circle cx="60" cy="60" r={r} stroke="rgba(255,77,61,0.35)" strokeWidth="10" fill="none" />
      <circle
        cx="60"
        cy="60"
        r={r}
        stroke="var(--gold)"
        strokeWidth="10"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={`${c * share} ${c}`}
        transform="rotate(-90 60 60)"
        className="donut-arc"
        style={{ ['--len' as string]: `${c * share}` }}
      />
      <text x="60" y="58" textAnchor="middle" className="donut-v">{Math.round(share * 100)}%</text>
      <text x="60" y="76" textAnchor="middle" className="donut-l">ELIGIBLE</text>
    </svg>
  )
}

export function DebtorReconciliationCard({ debtorReconciliation: d, consistency }: Props) {
  if (!d && !consistency) return null

  return (
    <>
      {d && (
        <div className="panel panel-pad debtors">
          <div className="card-head">
            <span className="label">Debtor reconciliation · invoice by invoice</span>
            <span className="chip chip-muted">{d.invoices.length} invoices</span>
          </div>

          <div className="debtor-top">
            <Donut eligible={d.total_eligible_outstanding} total={d.total_outstanding} />
            <div className="debtor-figs">
              <div>
                <div className="label">Total outstanding</div>
                <CountUp value={d.total_outstanding} format={inr} className="num recon-v" />
              </div>
              <div>
                <div className="label">Eligible for DP</div>
                <CountUp value={d.total_eligible_outstanding} format={inr} className="num recon-v gold" />
              </div>
              <div>
                <div className="label">Excluded</div>
                <CountUp value={d.total_outstanding - d.total_eligible_outstanding} format={inr} className="num recon-v red" />
              </div>
            </div>
          </div>

          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Date</th>
                  <th className="r">Amount</th>
                  <th className="r">Balance</th>
                  <th>Status</th>
                  <th className="r">Age</th>
                  <th>Eligible</th>
                </tr>
              </thead>
              <tbody>
                {d.invoices.map((inv, i) => (
                  <tr key={inv.invoice_id} style={{ ['--i' as string]: i }} className="row-in">
                    <td className="mono">{inv.invoice_id}</td>
                    <td className="mut">{inv.date}</td>
                    <td className="r num">{inr(inv.amount)}</td>
                    <td className="r num">{inr(inv.balance)}</td>
                    <td><span className={`pill pill-${inv.status}`}>{inv.status}</span></td>
                    <td className="r num">
                      <span className={inv.age_days > 90 ? 'red' : ''}>{inv.age_days} d</span>
                    </td>
                    <td>
                      {inv.balance <= 0 ? (
                        <span className="mut">paid</span>
                      ) : inv.eligible ? (
                        <span className="chip chip-supported">yes</span>
                      ) : (
                        <span className="chip chip-ineligible_contradicted">no</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {d.duplicate_invoices.length > 0 && (
            <div className="warn-banner" style={{ marginTop: 12 }}>
              {d.duplicate_invoices.length} duplicate invoice(s) excluded:{' '}
              {d.duplicate_invoices.map((x) => `${x.invoice_id} (${inr(x.excluded_amount)})`).join(', ')}
            </div>
          )}
          {d.unallocated_receipts.length > 0 && (
            <div className="warn-banner" style={{ marginTop: 8 }}>
              {d.unallocated_receipts.length} unallocated receipt(s):{' '}
              {d.unallocated_receipts.map((x) => `${x.receipt_id} (${inr(x.amount)}): ${x.reason}`).join('; ')}
            </div>
          )}
        </div>
      )}

      {consistency && consistency.flags.length > 0 && (
        <div className="panel panel-pad variance">
          <div className="card-head">
            <span className="label">Period-over-period variance</span>
            <span className="chip chip-unresolved">{consistency.flags.length} flags</span>
          </div>
          <div className="variance-grid">
            {consistency.flags.map((f, i) => (
              <Reveal i={i} key={i}>
                <div className="var-card">
                  <div className={`var-pct num ${f.pct_change >= 0 ? 'amber' : 'red'}`}>
                    {Number.isFinite(f.pct_change) ? `${f.pct_change > 0 ? '+' : ''}${f.pct_change.toFixed(1)}%` : 'new'}
                  </div>
                  <div className="var-field">{humanize(f.field)}</div>
                  <div className="var-route">
                    <span className="num">{inr(f.from_value)}</span>
                    <span className="var-arrow">→</span>
                    <span className="num">{inr(f.to_value)}</span>
                  </div>
                  <div className="label">
                    {f.from_period} → {f.to_period}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
