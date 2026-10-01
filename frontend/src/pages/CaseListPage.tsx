import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import type { Case } from '../types'

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
    setCreating(true)
    setError(null)
    try {
      await api.createCase({ name: name.trim(), business_name: businessName.trim() || undefined })
      setName('')
      setBusinessName('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create case')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="lobby">
      <header className="lobby-header">
        <div className="lobby-brand">
          <span className="brand-mark">क</span>
          <div>
            <h1>
              KARBHARI <span className="hindi">कारभारी</span>
            </h1>
            <p>Working Capital Guardian</p>
          </div>
        </div>
      </header>

      <div className="lobby-body">
        <div className="lobby-intro">
          <h2>Cases</h2>
          <p>Every working-capital investigation starts here.</p>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <form className="lobby-new-case" onSubmit={handleCreate}>
          <input
            placeholder="Case name (e.g. Q3 CC facility review)"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            placeholder="Business name (optional)"
            value={businessName}
            onChange={(e) => setBusinessName(e.target.value)}
          />
          <button className="btn" type="submit" disabled={!name.trim() || creating}>
            {creating ? 'Creating…' : 'New case'}
          </button>
        </form>

        {loading ? (
          <div className="empty-state">Loading cases…</div>
        ) : cases.length === 0 ? (
          <div className="empty-state">No cases yet. Create one above to begin.</div>
        ) : (
          <div className="case-grid">
            {cases.map((c) => (
              <Link key={c.id} to={`/cases/${c.id}`} className="case-card">
                <div className="case-card-top">
                  <span className="case-card-name">{c.name}</span>
                  <span className="status-pill">{c.status}</span>
                </div>
                <div className="case-card-business">
                  {c.business_name ?? 'No business name on file'}
                </div>
                <div className="case-card-date">
                  Opened {new Date(c.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
