import { useEffect, useState } from 'react'
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
import { DottedGlowBackground } from '../components/DottedGlowBackground'
import type { Case, Evidence, Investigation } from '../types'

// Ordered to match the product's real visual hierarchy: the graded
// discoveries first, the math/detail behind them second, the raw evidence
// that feeds it third, how the investigation got there fourth, and
// corrective actions last.
const NAV_ITEMS = [
  { key: 'findings', label: 'Findings' },
  { key: 'investigation', label: 'Investigation' },
  { key: 'evidence', label: 'Evidence' },
  { key: 'trace', label: 'How it investigated' },
  { key: 'actions', label: 'Actions' },
]

export function CaseWorkspacePage() {
  const { caseId } = useParams<{ caseId: string }>()
  const [activeTab, setActiveTab] = useState('findings')
  const [kase, setKase] = useState<Case | null>(null)
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [error, setError] = useState<string | null>(null)
  const [runningInvestigation, setRunningInvestigation] = useState(false)

  function loadAll() {
    if (!caseId) return
    api.getCase(caseId).then(setKase).catch((err) => setError(err.message))
    api.listEvidence(caseId).then(setEvidence).catch((err) => setError(err.message))
    api.listEvidenceCategories(caseId).then(setCategories).catch(() => undefined)
    api.listInvestigations(caseId).then(setInvestigations).catch(() => undefined)
  }

  useEffect(loadAll, [caseId])

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
    setRunningInvestigation(true)
    setError(null)
    try {
      await api.runInvestigation(caseId)
      loadAll()
      setActiveTab('findings')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Investigation failed to start')
    } finally {
      setRunningInvestigation(false)
    }
  }

  if (!kase) {
    return <div className="empty-state">Loading case…</div>
  }

  const latestInvestigation = investigations[0] ?? null

  return (
    <div className="console-shell">
      <aside className="console-rail">
        <DottedGlowBackground className="rail-canvas" />
        <div className="rail-content">
          <Link to="/" className="rail-brand">
            <span className="rail-brand-mark">क</span>
            <div>
              <div className="rail-brand-name">KARBHARI</div>
              <div className="rail-brand-sub">Working Capital Guardian</div>
            </div>
          </Link>

          <div className="rail-case">
            <Link to="/" className="rail-back">
              ← All cases
            </Link>
            <h2 className="rail-case-name">{kase.name}</h2>
            <div className="rail-case-meta">
              <span className="status-pill status-pill-dark">{kase.status}</span>
              <span>{kase.business_name ?? 'No business name on file'}</span>
            </div>
          </div>

          <WorkingCapitalHero investigation={latestInvestigation} onViewFindings={() => setActiveTab('findings')} />

          <SidebarNav items={NAV_ITEMS} active={activeTab} onChange={setActiveTab} />

          <button
            className="btn rail-run-btn"
            onClick={handleRunInvestigation}
            disabled={runningInvestigation}
          >
            {runningInvestigation ? 'Running…' : 'Run investigation'}
          </button>
        </div>
      </aside>

      <main className="console-main">
        {error && <div className="error-banner">{error}</div>}

        {activeTab === 'findings' && (
          <section>
            <h3 className="section-heading">Findings</h3>
            {!latestInvestigation?.details ? (
              <div className="card">
                <div className="empty-state">
                  No findings yet — attach evidence and run an investigation from the panel on the
                  left.
                </div>
              </div>
            ) : (
              <FindingsList findings={latestInvestigation.details.findings} />
            )}
          </section>
        )}

        {activeTab === 'investigation' && (
          <section>
            <h3 className="section-heading">Investigation detail</h3>
            {!latestInvestigation ? (
              <div className="card">
                <div className="empty-state">
                  No investigation has been run yet. Attach evidence, then run an investigation.
                </div>
              </div>
            ) : (
              <>
                <div className="card">
                  <p className="muted" style={{ fontSize: 12.5 }}>
                    Status: {latestInvestigation.status} · considered{' '}
                    {latestInvestigation.evidence_count_considered} evidence item(s) · started{' '}
                    {new Date(latestInvestigation.started_at).toLocaleString()}
                  </p>
                  <p className="summary-text">{latestInvestigation.summary}</p>
                </div>
                <div className="investigation-grid">
                  {latestInvestigation.details?.reconciliation && (
                    <ReconciliationCard reconciliation={latestInvestigation.details.reconciliation} />
                  )}
                  {latestInvestigation.details && (
                    <DebtorReconciliationCard
                      debtorReconciliation={latestInvestigation.details.debtor_reconciliation}
                      consistency={latestInvestigation.details.consistency}
                    />
                  )}
                </div>
              </>
            )}
          </section>
        )}

        {activeTab === 'evidence' && (
          <section>
            <h3 className="section-heading">Evidence</h3>
            <div className="card">
              <EvidenceUploader categories={categories} onUpload={handleUpload} />
              <div style={{ marginTop: 16 }}>
                <EvidenceList evidence={evidence} onDelete={handleDelete} />
              </div>
            </div>
          </section>
        )}

        {activeTab === 'trace' && (
          <section>
            <h3 className="section-heading">How it investigated</h3>
            <div className="card">
              {!latestInvestigation?.details ? (
                <div className="empty-state">
                  No investigation trace yet — run an investigation from the panel on the left.
                </div>
              ) : (
                <ToolTrace trace={latestInvestigation.details.tool_trace} />
              )}
            </div>
          </section>
        )}

        {activeTab === 'actions' && (
          <section>
            <h3 className="section-heading">Actions</h3>
            <div className="card">
              <div className="empty-state">
                The evidence pack and recommended corrective actions ship in a later phase.
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
