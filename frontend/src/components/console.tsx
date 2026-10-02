import { useEffect, useMemo, useState } from 'react'
import type { Evidence, Investigation } from '../types'
import { categoryColor, inr, lakh } from '../lib/format'
import { CountUp, Reveal } from './fx'
import { Icon } from './Icon'

/** Real numbers from the latest investigation, always visible above every tab. */
export function KpiStrip({ investigation, evidenceCount }: { investigation: Investigation | null; evidenceCount: number }) {
  const r = investigation?.details?.reconciliation
  const findings = investigation?.details?.findings ?? []
  const n = (s: string) => findings.filter((f) => f.status === s).length
  const sup = n('supported')
  const unr = n('unresolved')
  const con = n('ineligible_contradicted')
  const total = Math.max(1, findings.length)
  const ok = r?.can_calculate

  const tiles = [
    { l: 'Calculated DP', v: ok ? r?.calculated_dp ?? null : null, c: '' },
    { l: 'Bank recognises', v: ok ? r?.comparison_value ?? null : null, c: 'mut' },
    { l: 'Capacity gap', v: ok ? r?.gap ?? null : null, c: (r?.gap ?? 0) > 0 ? 'gold glow-gold' : '' },
  ]

  return (
    <div className="kpis">
      {tiles.map((t, i) => (
        <Reveal i={i} key={t.l}>
          <div className="kpi panel">
            <div className="label">{t.l}</div>
            {t.v === null || t.v === undefined ? (
              <div className="kpi-v num dim">—</div>
            ) : (
              <CountUp value={t.v} format={(x) => lakh(x)} className={`kpi-v num ${t.c}`} />
            )}
          </div>
        </Reveal>
      ))}
      <Reveal i={3}>
        <div className="kpi panel">
          <div className="label">Findings</div>
          <div className="kpi-v num">{findings.length || '—'}</div>
          <div className="mix-bar" title={`${sup} supported · ${unr} unresolved · ${con} contradicted`}>
            <i style={{ width: `${(sup / total) * 100}%`, background: 'var(--grn)' }} />
            <i style={{ width: `${(unr / total) * 100}%`, background: 'var(--amber)' }} />
            <i style={{ width: `${(con / total) * 100}%`, background: 'var(--red)' }} />
          </div>
        </div>
      </Reveal>
      <Reveal i={4}>
        <div className="kpi panel">
          <div className="label">Evidence</div>
          <div className="kpi-v num">{evidenceCount}</div>
          <div className="label kpi-sub">documents attached</div>
        </div>
      </Reveal>
    </div>
  )
}

/** Full-screen "agent at work" moment while an investigation runs. */
export function ScanOverlay({ evidence }: { evidence: Evidence[] }) {
  const steps = useMemo(
    () => [
      ['list_evidence', `${evidence.length} documents in case`],
      ...evidence.map((e) => ['read_evidence', e.original_filename]),
      ['check_consistency', 'comparing periods'],
      ['reconcile_debtors', 'rebuilding the debtor book'],
      ['calculate_drawing_power', 'margins · creditors · limit'],
      ['finish', 'grading findings'],
    ],
    [evidence],
  )
  const [i, setI] = useState(0)
  const [secs, setSecs] = useState(0)
  useEffect(() => {
    const a = window.setInterval(() => setI((x) => Math.min(x + 1, steps.length - 1)), 1700)
    const b = window.setInterval(() => setSecs((s) => s + 1), 1000)
    return () => {
      window.clearInterval(a)
      window.clearInterval(b)
    }
  }, [steps.length])

  const docs = evidence.length ? evidence.slice(0, 6) : []
  return (
    <div className="scan-overlay" role="status" aria-live="polite">
      <div className="scan-inner">
        <div className="kicker">Investigation in progress · {secs}s</div>
        <h2 className="display scan-title">
          <span className="slam">READ.</span> <span className="slam" style={{ ['--i' as string]: 1 }}>CROSS-CHECK.</span>{' '}
          <span className="slam gold" style={{ ['--i' as string]: 2 }}>VERIFY.</span>
        </h2>
        <div className="scan-docs">
          {(docs.length ? docs : [null, null, null, null, null]).map((d, k) => (
            <div key={k} className={`scan-doc${k < i ? ' read' : ''}`} style={{ ['--c' as string]: d ? categoryColor(d.category) : 'var(--mut)' }}>
              <span className="doc-strip" />
              <div className="doc-lines">
                <i style={{ width: '70%' }} />
                <i style={{ width: '50%' }} />
                <i style={{ width: '85%' }} />
                <i style={{ width: '40%' }} />
                <i style={{ width: '62%' }} />
              </div>
              <span className="scan-doc-name">{d ? d.original_filename : 'document'}</span>
              {k < i && <Icon name="check" size={16} className="scan-check" />}
            </div>
          ))}
          <span className="scan-beam" />
        </div>
        <ul className="scan-log">
          {steps.slice(0, i + 1).slice(-5).map(([tool, text], k, arr) => (
            <li key={`${tool}-${text}-${k}`} className={k === arr.length - 1 ? 'live' : ''}>
              <span className="feed-tool">{tool}</span>
              <span>{text}</span>
            </li>
          ))}
        </ul>
        <div className="scan-progress">
          <i />
        </div>
        {secs >= 30 && (
          <p className="scan-slow label">
            The model is taking longer than usual · still investigating, results will appear here
          </p>
        )}
      </div>
    </div>
  )
}

/** The Actions tab: planned deliverables, clearly marked as the next phase. */
export function ActionsPreview({ investigation, businessName }: { investigation: Investigation | null; businessName: string | null }) {
  const gap = investigation?.details?.reconciliation?.gap
  const cards = [
    { icon: 'bank', t: 'Draft note to your bank', d: 'A polite, evidence-backed request to recompute Drawing Power, citing the exact document lines.' },
    { icon: 'doc', t: 'Evidence pack (PDF)', d: 'Every finding with its source quotes, the reconciliation tables and the calculation, ready to share with your CA.' },
    { icon: 'check', t: 'Follow-up checklist', d: 'What to fix before the next stock statement: aged debtors to chase, receipts to tag, figures to confirm.' },
    { icon: 'spark', t: 'Monthly watch', d: 'Re-run automatically when a new stock statement arrives and alert you if capacity slips.' },
  ]
  return (
    <div className="actions">
      <div className="action-cards">
        {cards.map((c, i) => (
          <Reveal i={i} key={c.t}>
            <div className="action panel panel-pad">
              <div className="action-top">
                <span className="action-icon">
                  <Icon name={c.icon} size={20} />
                </span>
                <span className="chip chip-muted">next phase</span>
              </div>
              <h4>{c.t}</h4>
              <p className="mut">{c.d}</p>
            </div>
          </Reveal>
        ))}
      </div>
      <Reveal i={4}>
        <div className="letter panel">
          <div className="letter-head">
            <span className="label">Preview · draft note to bank</span>
            <span className="chip chip-gold">coming next</span>
          </div>
          <div className="letter-body">
            <p>To the Branch Manager,</p>
            <p>
              Re: Drawing Power on our cash-credit facility{businessName ? ` (${businessName})` : ''}.
            </p>
            <p>
              Based on our latest stock statement, debtor records and the margins in our sanction letter, our Drawing
              Power appears to be{' '}
              <b className="gold">{gap && gap > 0 ? `${inr(gap)} higher` : 'different from'}</b> than the figure currently recognised.
              We attach the supporting calculation and source documents for your review…
            </p>
            <div className="letter-fade" />
          </div>
        </div>
      </Reveal>
    </div>
  )
}
