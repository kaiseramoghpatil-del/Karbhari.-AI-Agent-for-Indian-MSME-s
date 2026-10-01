import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { Tabs } from '../components/Tabs'
import { EvidenceUploader } from '../components/EvidenceUploader'
import { EvidenceList } from '../components/EvidenceList'
import { ReconciliationCard } from '../components/ReconciliationCard'
import { DebtorReconciliationCard } from '../components/DebtorReconciliationCard'
import { FindingsList } from '../components/FindingsList'
import { ToolTrace } from '../components/ToolTrace'
import { WorkingCapitalHero } from '../components/WorkingCapitalHero'
import type { Case, Evidence, Investigation } from '../types'

// Ordered to match the product's real visual hierarchy: the graded
// discoveries first, the math/detail behind them second, the raw evidence
// that feeds it third, how the investigation got there fourth, and
// corrective actions last.
const TABS = [
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
  const tabsRef = useRef<HTMLDivElement>(null)

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

  function handleViewFindings() {
    setActiveTab('findings')
    tabsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  if (!kase) {
    return <div className="empty-state">Loading case…</div>
  }

  const latestInvestigation = investigations[0] ?? null

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/" className="muted" style={{ fontSize: 12.5 }}>
            ← All cases
          </Link>
          <h2 style={{ marginTop: 6 }}>
            {kase.name} <span className="status-pill">{kase.status}</span>
          </h2>
          <p>{kase.business_name ?? 'No business name on file'}</p>
        </div>
        <button className="btn" onClick={handleRunInvestigation} disabled={runningInvestigation}>
          {runningInvestigation ? 'Running…' : 'Run investigation'}
        </button>
      </div>

      <WorkingCapitalHero investigation={latestInvestigation} onViewFindings={handleViewFindings} />

      {error && <div className="error-banner">{error}</div>}

      <div ref={tabsRef}>
        <Tabs tabs={TABS} active={activeTab} onChange={setActiveTab} />
      </div>

      {activeTab === 'findings' && (
        <div>
          {!latestInvestigation?.details ? (
            <div className="card">
              <div className="empty-state">
                No findings yet — attach evidence and run an investigation above.
              </div>
            </div>
          ) : (
            <FindingsList findings={latestInvestigation.details.findings} />
          )}
        </div>
      )}

      {activeTab === 'investigation' && (
        <div>
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
              {latestInvestigation.details?.reconciliation && (
                <ReconciliationCard reconciliation={latestInvestigation.details.reconciliation} />
              )}
              {latestInvestigation.details && (
                <DebtorReconciliationCard
                  debtorReconciliation={latestInvestigation.details.debtor_reconciliation}
                  consistency={latestInvestigation.details.consistency}
                />
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'evidence' && (
        <div className="card">
          <EvidenceUploader categories={categories} onUpload={handleUpload} />
          <div style={{ marginTop: 16 }}>
            <EvidenceList evidence={evidence} onDelete={handleDelete} />
          </div>
        </div>
      )}

      {activeTab === 'trace' && (
        <div className="card">
          {!latestInvestigation?.details ? (
            <div className="empty-state">
              No investigation trace yet — run an investigation from the Investigation tab first.
            </div>
          ) : (
            <ToolTrace trace={latestInvestigation.details.tool_trace} />
          )}
        </div>
      )}

      {activeTab === 'actions' && (
        <div className="card">
          <div className="empty-state">
            The evidence pack and recommended corrective actions ship in a later phase.
          </div>
        </div>
      )}
    </div>
  )
}
