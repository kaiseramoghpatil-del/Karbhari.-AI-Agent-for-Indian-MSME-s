import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Chrome } from '../components/Chrome'
import { Backdrop, CountUp, Reveal, Sparkline, Ticker } from '../components/fx'
import { Icon } from '../components/Icon'
import { inr } from '../lib/format'
import { sfx } from '../lib/sound'
import type { Case } from '../types'

// Illustrative agent activity for the lobby's ambient feed. Clearly labelled
// "sample" in the UI; real traces live in each case's "How it investigated" tab.
const SAMPLE_FEED = [
  ['list_evidence', '6 documents in case'],
  ['read_evidence', 'sanction_letter.pdf · limit ₹50,00,000'],
  ['read_evidence', 'stock_statement_sep2026.pdf · stock ₹30,00,000'],
  ['check_consistency', 'stock value +25.0% Jun → Sep'],
  ['reconcile_debtors', '6 invoices · 3 receipts · per debtor'],
  ['flag', 'INV-1005 · 107 days · past 90-day cut-off'],
  ['flag', 'INV-1002 · 152 days · excluded'],
  ['calculate_drawing_power', 'calculated ₹25,70,000'],
  ['finding', 'gap ₹2,20,000 · supported'],
  ['read_evidence', 'debtor_invoice_ledger.xlsx · 6 rows'],
  ['check_consistency', 'sundry creditors +33.3%'],
  ['finding', 'ineligible debtors ₹6,00,000 · supported'],
]

const TICKER = [
  <><b>READ</b> every document</>,
  <><b>CROSS-CHECK</b> every number</>,
  <><b>PROVE</b> every rupee</>,
  <>sanction letter · <b>margins &amp; limit</b></>,
  <>stock statements · <b>period swings</b></>,
  <>debtor ageing · <b>90-day cut-off</b></>,
  <>receipts · <b>FIFO per debtor</b></>,
  <>duplicate invoices · <b>excluded</b></>,
  <>drawing power · <b>computed in code</b></>,
  <>findings · <b>graded &amp; cited</b></>,
]

const STEPS = [
  { n: '01', t: 'READ', d: 'The agent opens every file you attach: sanction letter, stock statements, ledgers, receipts.' },
  { n: '02', t: 'CROSS-CHECK', d: 'Sources are tested against each other. Debtors are rebuilt invoice by invoice.' },
  { n: '03', t: 'VERIFY', d: 'Tested Python computes Drawing Power. Every finding is graded and cited.' },
]

const CATCHES = [
  ['Stale stock statements', 'red'],
  ['Debtors past the cut-off', 'red'],
  ['Duplicate invoices', 'amber'],
  ['Unallocated receipts', 'amber'],
  ['Unexplained period swings', 'amber'],
  ['Placeholder margins', 'amber'],
  ['Unused drawing power', 'gold'],
  ['Creditor deductions', 'teal'],
]

function AgentFeed() {
  const [head, setHead] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => setHead((h) => h + 1), 2100)
    return () => window.clearInterval(id)
  }, [])
  const rows = Array.from({ length: 6 }, (_, k) => {
    const idx = (head - k + SAMPLE_FEED.length * 100) % SAMPLE_FEED.length
    return { key: head - k, tool: SAMPLE_FEED[idx][0], text: SAMPLE_FEED[idx][1] }
  })
  return (
    <div className="feed panel panel-glass">
      <div className="feed-head">
        <span className="label">Agent feed</span>
        <span className="chip chip-muted">sample</span>
      </div>
      <ul>
        {rows.map((r, i) => (
          <li key={r.key} className={i === 0 ? 'feed-new' : ''} style={{ opacity: 1 - i * 0.14 }}>
            <span className={`feed-tool feed-${r.tool}`}>{r.tool}</span>
            <span className="feed-text">{r.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function CaseListPage() {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [name, setName] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [creating, setCreating] = useState(false)

  function load() {
    setLoading(true)
    api
      .listCases()
      .then(setCases)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    sfx.click()
    setCreating(true)
    setError(null)
    try {
      await api.createCase({ name: name.trim(), business_name: businessName.trim() || undefined })
      setName('')
      setBusinessName('')
      sfx.chime()
      load()
    } catch (err) {
      sfx.buzz()
      setError(err instanceof Error ? err.message : 'Failed to create case')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="page">
      <Backdrop tint="gold" />
      <Chrome section="Lobby" brandLink={false} />

      <main className="lobby">
        <section className="hero">
          <div className="hero-copy">
            <Reveal i={0}>
              <div className="kicker">कारभारी · Working Capital Guardian</div>
            </Reveal>
            <h1 className="display hero-title">
              <span className="slam" style={{ ['--i' as string]: 0 }}>FIND WHAT</span>{' '}
              <span className="slam" style={{ ['--i' as string]: 1 }}>YOUR NUMBERS</span>{' '}
              <span className="slam" style={{ ['--i' as string]: 2 }}>ARE</span>{' '}
              <span className="slam gold glow-gold" style={{ ['--i' as string]: 3 }}>HIDING.</span>
            </h1>
            <Reveal i={4}>
              <p className="hero-lede">
                An AI investigator for Indian MSMEs. It reads your bank-facility evidence, rebuilds your Drawing Power
                with tested code, and shows the evidence behind every rupee.
              </p>
            </Reveal>

            <Reveal i={5}>
              <form className="new-case panel panel-glass" onSubmit={handleCreate}>
                <div className="new-case-head">
                  <span className="label">Open a new case</span>
                  <span className="label dim-label">30 s to 2 min per investigation</span>
                </div>
                <div className="new-case-row">
                  <input
                    className="input"
                    placeholder="Case name, e.g. Q3 Drawing Power review"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <input
                    className="input"
                    placeholder="Business name (optional)"
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                  />
                  <button className="btn" type="submit" disabled={!name.trim() || creating}>
                    {creating ? 'Opening…' : 'Open case'} <Icon name="arrow" size={16} />
                  </button>
                </div>
              </form>
            </Reveal>
            {error && <div className="error-banner" style={{ marginTop: 14 }}>{error}</div>}
          </div>

          <div className="hero-side">
            <Reveal i={2}>
              <div className="bench panel panel-glass">
                <div className="bench-top">
                  <span className="label">Verified benchmark</span>
                  <span className="chip chip-supported"><span className="chip-dot" />matched by hand</span>
                </div>
                <div className="bench-figure num gold glow-gold">
                  <CountUp value={1210000} format={inr} duration={1800} />
                </div>
                <div className="label bench-caption">Drawing-power gap found · 7-document case</div>
                <div className="bench-bars">
                  <div className="bench-row">
                    <span className="label">Bank recognised</span>
                    <div className="bar"><i style={{ width: '72.6%', background: 'var(--red)' }} /></div>
                    <span className="num">₹32.00 L</span>
                  </div>
                  <div className="bench-row">
                    <span className="label">KARBHARI</span>
                    <div className="bar"><i className="bar-gold" style={{ width: '100%' }} /></div>
                    <span className="num gold">₹44.10 L</span>
                  </div>
                </div>
              </div>
            </Reveal>
            <Reveal i={3}>
              <AgentFeed />
            </Reveal>
          </div>
        </section>

        <Ticker items={TICKER} />

        <section className="stats">
          {[
            { v: cases.length, f: (n: number) => Math.round(n).toString(), l: 'Cases in this workspace', c: '' },
            { v: 52, f: (n: number) => Math.round(n).toString(), l: 'Automated tests passing', c: 'grn' },
            { v: 20, f: (n: number) => Math.round(n).toString(), l: 'Max agent steps · bounded', c: '' },
            { v: 0, f: () => '0', l: 'Rupee figures from the LLM', c: 'gold' },
          ].map((s, i) => (
            <Reveal i={i} key={s.l}>
              <div className="stat">
                <CountUp value={s.v} format={s.f} className={`stat-v num ${s.c}`} />
                <div className="label">{s.l}</div>
              </div>
            </Reveal>
          ))}
        </section>

        <section className="cases-section">
          <div className="section-head">
            <div>
              <div className="kicker">01 · Your cases</div>
              <h2 className="display section-title">Every investigation starts here.</h2>
            </div>
            <span className="label">{cases.length} open</span>
          </div>

          {loading ? (
            <div className="case-grid">
              {[0, 1, 2].map((i) => (
                <div key={i} className="case-card skeleton" />
              ))}
            </div>
          ) : cases.length === 0 ? (
            <div className="empty panel panel-pad">
              <Icon name="spark" size={28} className="gold" />
              <div>
                <h3>No cases yet</h3>
                <p className="mut">Open one above, attach the six files in <code>ASSETS FOR TESTING</code>, and run an investigation.</p>
              </div>
            </div>
          ) : (
            <div className="case-grid">
              {cases.map((c, i) => (
                <Reveal i={i} key={c.id}>
                  <Link to={`/cases/${c.id}`} className="case-card panel" onClick={() => sfx.whoosh()} onMouseEnter={() => sfx.tick()}>
                    <span className="case-strip" />
                    <div className="case-top">
                      <span className="chip chip-gold">{c.status}</span>
                      <span className="label">#{c.id.slice(0, 6)}</span>
                    </div>
                    <h3 className="case-name">{c.name}</h3>
                    <div className="case-biz">{c.business_name ?? 'No business name on file'}</div>
                    <Sparkline seed={c.id} />
                    <div className="case-foot">
                      <span className="label">
                        Opened {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </span>
                      <span className="case-open">Open <Icon name="arrow" size={14} /></span>
                    </div>
                  </Link>
                </Reveal>
              ))}
              <Reveal i={cases.length}>
                <button
                  type="button"
                  className="case-card case-new"
                  onClick={() => {
                    sfx.click()
                    window.scrollTo({ top: 0, behavior: 'smooth' })
                    window.setTimeout(() => document.querySelector<HTMLInputElement>('.new-case .input')?.focus(), 450)
                  }}
                >
                  <span className="case-new-plus">+</span>
                  <span className="case-new-title">Open another case</span>
                  <span className="label">Each review gets its own evidence and trace</span>
                </button>
              </Reveal>
            </div>
          )}
        </section>

        <section className="how">
          <div className="section-head">
            <div>
              <div className="kicker">02 · How it works</div>
              <h2 className="display section-title">The model reasons. <span className="gold">Python calculates.</span></h2>
            </div>
          </div>
          <div className="steps">
            {STEPS.map((s, i) => (
              <Reveal i={i} key={s.n}>
                <div className="step panel panel-pad">
                  <div className="step-n num">{s.n}</div>
                  <div className="display step-t">{s.t}</div>
                  <p className="mut">{s.d}</p>
                  <div className="step-bar"><i style={{ animationDelay: `${i * 0.6}s` }} /></div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        <section className="catches">
          <div className="section-head">
            <div>
              <div className="kicker">03 · What it catches</div>
              <h2 className="display section-title">Errors in <span className="gold">both</span> directions.</h2>
            </div>
          </div>
          <div className="catch-grid">
            {CATCHES.map(([t, c], i) => (
              <Reveal i={i} key={t}>
                <div className={`catch catch-${c}`}>
                  <span className="catch-dot" />
                  {t}
                </div>
              </Reveal>
            ))}
          </div>
        </section>

        <footer className="lobby-foot">
          <span className="display foot-mark">KARBHARI</span>
          <span className="label">Read every document · Cross-check every number · Prove every rupee</span>
          <span className="label">Built for Indian MSMEs</span>
        </footer>
      </main>
    </div>
  )
}
