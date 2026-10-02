import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { SidebarNav } from '../components/SidebarNav'
import { EvidenceUploader } from '../components/EvidenceUploader'
import { EvidenceList } from '../components/EvidenceList'
import { ReconciliationCard } from '../components/ReconciliationCard'
import { DebtorReconciliationCard } from '../components/DebtorReconciliationCard'
import { FindingsList } from '../components/FindingsList'
import { ToolTrace } from '../components/ToolTrace'
import { WorkingCapitalHero } from '../components/WorkingCapitalHero'
import { Chrome } from '../components/Chrome'
import { Backdrop, Ticker, type Tint } from '../components/fx'
import { ActionsPreview, KpiStrip, ScanOverlay } from '../components/console'
import { Icon } from '../components/Icon'
import { sfx } from '../lib/sound'
import type { Case, Evidence, Investigation } from '../types'

// Ordered to match the product's real visual hierarchy: graded discoveries
// first, the math behind them, the evidence, how the agent got there, actions.
const TABS = [
  { key: 'findings', label: 'Findings', icon: 'findings', title: 'What the evidence shows' },
  { key: 'investigation', label: 'Investigation', icon: 'investigation', title: 'Every figure, in full' },
  { key: 'evidence', label: 'Evidence', icon: 'evidence', title: 'Nothing taken on trust' },
  { key: 'trace', label: 'How it investigated', icon: 'trace', title: 'The agent, step by step' },
  { key: 'actions', label: 'Actions', icon: 'actions', title: 'From finding to action' },
]

export function CaseWorkspacePage() {
  const { caseId } = useParams<{ caseId: string }>()
  const [activeTab, setActiveTab] = useState('findings')
  const [kase, setKase] = useState<Case | null>(null)
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)
  const [celebrate, setCelebrate] = useState(0)
  const stopScan = useRef<(() => void) | null>(null)

  function loadAll() {
    if (!caseId) return
    api.getCase(caseId).then(setKase).catch((err) => setError(err.message))
    api.listEvidence(caseId).then(setEvidence).catch((err) => setError(err.message))
    api.listEvidenceCategories(caseId).then(setCategories).catch(() => undefined)
    api.listInvestigations(caseId).then(setInvestigations).catch(() => undefined)
  }

  useEffect(loadAll, [caseId])
  useEffect(() => () => stopScan.current?.(), [])

  function switchTab(key: string) {
    sfx.whoosh()
    setActiveTab(key)
  }

  async function handleUpload(file: File, category: string) {
    if (!caseId) return
    await api.uploadEvidence(caseId, file, category)
    loadAll()
  }

  async function handleDelete(evidenceId: string) {
    if (!caseId) return
    await api.deleteEvidence(caseId, evidenceId)
    loadAll()
  }

  async function handleRunInvestigation() {
    if (!caseId) return
    sfx.slam()
    setRunning(true)
    setError(null)
    stopScan.current = sfx.scanLoop()
    try {
      const inv = await api.runInvestigation(caseId)
      stopScan.current?.()
      const gap = inv.details?.reconciliation?.gap ?? 0
      if (inv.status === 'error') sfx.buzz()
      else {
        sfx.impact()
        if (gap > 0) window.setTimeout(() => sfx.chime(), 450)
      }
      setCelebrate((c) => c + 1)
      loadAll()
      setActiveTab('findings')
    } catch (err) {
      stopScan.current?.()
      sfx.buzz()
      setError(err instanceof Error ? err.message : 'Investigation failed to start')
    } finally {
      stopScan.current = null
      setRunning(false)
    }
  }

  if (!kase) {
    return (
      <div className="page">
        <Backdrop tint="blue" />
        <div className="loading-screen">
          <span className="display">KARBHARI</span>
          <div className="scan-progress"><i /></div>
        </div>
      </div>
    )
  }

  const latest = investigations[0] ?? null
  const details = latest?.details ?? null
  const gap = details?.reconciliation?.gap ?? null
  const tint: Tint = running ? 'teal' : latest?.status === 'error' ? 'red' : gap !== null && gap > 0 ? 'gold' : 'blue'
  const tab = TABS.find((t) => t.key === activeTab) ?? TABS[0]
  const tabIndex = TABS.indexOf(tab)
  const navItems = TABS.map((t) => ({
    ...t,
    badge:
      t.key === 'findings'
        ? details?.findings.length
        : t.key === 'evidence'
          ? evidence.length
          : t.key === 'trace'
            ? details?.tool_trace.length
            : undefined,
  }))

  const tickerItems = [
    <>case <b>{kase.name}</b></>,
    <>business <b>{kase.business_name ?? 'not on file'}</b></>,
    <>evidence <b>{evidence.length} documents</b></>,
    <>investigations run <b>{investigations.length}</b></>,
    <>last run <b>{latest ? new Date(latest.started_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) : 'never'}</b></>,
    <>engine <b>deterministic · tested</b></>,
    <>agent <b>bounded · 20 steps</b></>,
  ]

  return (
    <div className="page">
      <Backdrop tint={tint} />
      <div className="console">
        <aside className="rail">
          <Link to="/" className="rail-brand" onClick={() => sfx.click()}>
            <span className="rail-mark">क</span>
            <div>
              <div className="rail-name">KARBHARI</div>
              <div className="label">Working Capital Guardian</div>
            </div>
          </Link>

          <div className="rail-case">
            <Link to="/" className="rail-back" onClick={() => sfx.click()}>
              <Icon name="back" size={13} /> All cases
            </Link>
            <h2 className="rail-case-name">{kase.name}</h2>
            <div className="rail-case-meta">
              <span className="chip chip-gold">{kase.status}</span>
              <span className="mut">{kase.business_name ?? 'No business name on file'}</span>
            </div>
          </div>

          <WorkingCapitalHero investigation={latest} onViewFindings={() => switchTab('findings')} celebrate={celebrate} />

          <SidebarNav items={navItems} active={activeTab} onChange={switchTab} />

          <button className={`btn run-btn${running ? ' running' : ''}`} onClick={handleRunInvestigation} disabled={running}>
            <Icon name="play" size={15} />
            {running ? 'Investigating…' : latest ? 'Run again' : 'Run investigation'}
          </button>
          <div className="rail-foot label">
            {evidence.length === 0 ? 'Attach evidence first' : `${evidence.length} documents ready`}
          </div>
        </aside>

        <div className="main-col">
          <Chrome section={tab.label} />
          <Ticker items={tickerItems} slow />

          <main className="main">
            {error && (
              <div className="error-banner" style={{ marginBottom: 18 }}>
                <Icon name="x" size={16} /> {error}
              </div>
            )}

            <KpiStrip investigation={latest} evidenceCount={evidence.length} />

            <div className="view-head view-enter" key={`h-${activeTab}`}>
              <div className="kicker">
                0{tabIndex + 1} · {tab.label}
              </div>
              <h1 className="display view-title">{tab.title}</h1>
            </div>

            <section className="view view-enter" key={activeTab}>
              {activeTab === 'findings' &&
                (!details ? (
                  <EmptyCta onRun={handleRunInvestigation} canRun={evidence.length > 0} goEvidence={() => switchTab('evidence')} />
                ) : (
                  <FindingsList findings={details.findings} />
                ))}

              {activeTab === 'investigation' &&
                (!latest ? (
                  <EmptyCta onRun={handleRunInvestigation} canRun={evidence.length > 0} goEvidence={() => switchTab('evidence')} />
                ) : (
                  <div className="inv-stack">
                    <div className="summary panel panel-pad">
                      <div className="card-head">
                        <span className="label">Run summary</span>
                        <span className={`chip ${latest.status === 'complete' ? 'chip-supported' : 'chip-unresolved'}`}>
                          <span className="chip-dot" />
                          {latest.status}
                        </span>
                      </div>
                      <p className="summary-text">{latest.summary}</p>
                      <div className="label">
                        {latest.evidence_count_considered} documents considered · started{' '}
                        {new Date(latest.started_at).toLocaleString('en-IN')}
                      </div>
                    </div>
                    {details?.reconciliation && <ReconciliationCard reconciliation={details.reconciliation} />}
                    {details && (
                      <DebtorReconciliationCard debtorReconciliation={details.debtor_reconciliation} consistency={details.consistency} />
                    )}
                  </div>
                ))}

              {activeTab === 'evidence' && (
                <div className="evidence-stack">
                  <div className="evidence-top">
                    <div className="panel panel-pad">
                      <EvidenceUploader categories={categories} onUpload={handleUpload} />
                    </div>
                    <EvidenceChecklist evidence={evidence} />
                  </div>
                  <EvidenceList evidence={evidence} onDelete={handleDelete} />
                </div>
              )}

              {activeTab === 'trace' &&
                (!details ? (
                  <EmptyCta onRun={handleRunInvestigation} canRun={evidence.length > 0} goEvidence={() => switchTab('evidence')} />
                ) : (
                  <ToolTrace trace={details.tool_trace} />
                ))}

              {activeTab === 'actions' && <ActionsPreview investigation={latest} businessName={kase.business_name} />}
            </section>
          </main>
        </div>
      </div>

      {running && <ScanOverlay evidence={evidence} />}
    </div>
  )
}

// What a complete Drawing Power case needs, mapped to evidence categories.
const CHECKLIST: [string, string, string][] = [
  ['sanction_letter', 'Sanction letter', 'limit, margins, debtor cut-off'],
  ['stock_statement', 'Stock statements', 'two periods enable swing checks'],
  ['debtor_ledger', 'Debtor invoices & receipts', 'rebuilt invoice by invoice'],
  ['creditor_ledger', 'Creditor ledger', 'the creditor deduction'],
  ['bank_statement', 'Bank statement', 'the DP the bank recognises'],
]

function EvidenceChecklist({ evidence }: { evidence: Evidence[] }) {
  const count = (c: string) => evidence.filter((e) => e.category === c).length
  const done = CHECKLIST.filter(([c]) => count(c) > 0).length
  return (
    <div className="panel panel-pad checklist">
      <div className="card-head">
        <span className="label">Case completeness</span>
        <span className={`chip ${done === CHECKLIST.length ? 'chip-supported' : 'chip-gold'}`}>
          {done}/{CHECKLIST.length}
        </span>
      </div>
      <div className="bar" style={{ marginBottom: 14 }}>
        <i className="bar-gold" style={{ width: `${(done / CHECKLIST.length) * 100}%` }} />
      </div>
      <ul>
        {CHECKLIST.map(([c, l, hint]) => {
          const n = count(c)
          return (
            <li key={c} className={n ? 'ok' : ''}>
              <span className="ck">{n ? <Icon name="check" size={13} /> : null}</span>
              <span className="ck-l">
                {l}
                {n > 1 && <b className="num"> ×{n}</b>}
              </span>
              <span className="ck-h">{hint}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

function EmptyCta({ onRun, canRun, goEvidence }: { onRun: () => void; canRun: boolean; goEvidence: () => void }) {
  return (
    <div className="empty-cta panel">
      <div className="empty-art" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div>
        <div className="kicker">Nothing to show yet</div>
        <h3 className="display">{canRun ? 'Ready when you are.' : 'Start with the evidence.'}</h3>
        <p className="mut">
          {canRun
            ? 'Your documents are attached. Run the investigation and KARBHARI will read, cross-check and verify them.'
            : 'Attach the sanction letter, stock statements, ledgers and receipts. The six files in ASSETS FOR TESTING make a complete sample case.'}
        </p>
        {canRun ? (
          <button className="btn" onClick={onRun}>
            <Icon name="play" size={15} /> Run investigation
          </button>
        ) : (
          <button className="btn" onClick={goEvidence}>
            <Icon name="upload" size={15} /> Attach evidence
          </button>
        )}
      </div>
    </div>
  )
}
