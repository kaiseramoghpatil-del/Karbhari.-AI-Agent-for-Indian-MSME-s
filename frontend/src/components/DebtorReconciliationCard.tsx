import type { DebtorReconciliation, ConsistencyResult } from '../types'

function fmtMoney(n: number): string {
  return '₹' + n.toLocaleString('en-IN', { maximumFractionDigits: 2 })
}

interface Props {
  debtorReconciliation: DebtorReconciliation | null
  consistency: ConsistencyResult | null
}

export function DebtorReconciliationCard({ debtorReconciliation, consistency }: Props) {
  if (!debtorReconciliation && !consistency) return null

  return (
    <div className="card">
      <h3>Debtor reconciliation</h3>

      {debtorReconciliation && (
        <>
          <div className="dp-figures">
            <div>
              <span className="muted">Total outstanding</span>
              <div className="dp-value">{fmtMoney(debtorReconciliation.total_outstanding)}</div>
            </div>
            <div>
              <span className="muted">Eligible outstanding</span>
              <div className="dp-value dp-gap-positive">
                {fmtMoney(debtorReconciliation.total_eligible_outstanding)}
              </div>
            </div>
          </div>

          <table className="evidence-table">
            <thead>
              <tr>
                <th>Invoice</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Balance</th>
                <th>Status</th>
                <th>Age (days)</th>
                <th>Eligible</th>
              </tr>
            </thead>
            <tbody>
              {debtorReconciliation.invoices.map((inv) => (
                <tr key={inv.invoice_id}>
                  <td>{inv.invoice_id}</td>
                  <td>{inv.date}</td>
                  <td>{fmtMoney(inv.amount)}</td>
                  <td>{fmtMoney(inv.balance)}</td>
                  <td>{inv.status}</td>
                  <td>{inv.age_days}</td>
                  <td>{inv.eligible ? 'yes' : 'no'}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {debtorReconciliation.duplicate_invoices.length > 0 && (
            <div className="error-banner" style={{ marginTop: 12 }}>
              {debtorReconciliation.duplicate_invoices.length} duplicate invoice(s) excluded from
              totals:{' '}
              {debtorReconciliation.duplicate_invoices
                .map((d) => `${d.invoice_id} (${fmtMoney(d.excluded_amount)} excluded)`)
                .join(', ')}
            </div>
          )}

          {debtorReconciliation.unallocated_receipts.length > 0 && (
            <div className="error-banner" style={{ marginTop: 8 }}>
              {debtorReconciliation.unallocated_receipts.length} unallocated receipt(s):{' '}
              {debtorReconciliation.unallocated_receipts
                .map((r) => `${r.receipt_id} (${fmtMoney(r.amount)}) -- ${r.reason}`)
                .join('; ')}
            </div>
          )}
        </>
      )}

      {consistency && consistency.flags.length > 0 && (
        <div style={{ marginTop: debtorReconciliation ? 16 : 0 }}>
          <h4 style={{ margin: '0 0 6px', fontSize: 13.5 }}>Period-over-period variance</h4>
          <ul className="quote-list">
            {consistency.flags.map((f, i) => (
              <li key={i}>{f.message}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
