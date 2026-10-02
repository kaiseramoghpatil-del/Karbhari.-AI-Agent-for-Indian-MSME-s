import type { Evidence } from '../types'
import { categoryColor, humanize } from '../lib/format'
import { sfx } from '../lib/sound'
import { Reveal } from './fx'

interface EvidenceListProps {
  evidence: Evidence[]
  onDelete: (evidenceId: string) => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

/** Evidence as document cards with a coloured category strip, as in the film. */
export function EvidenceList({ evidence, onDelete }: EvidenceListProps) {
  if (evidence.length === 0) {
    return <div className="empty panel panel-pad">No evidence attached yet. Drop the six files from ASSETS FOR TESTING to try it.</div>
  }

  return (
    <div className="doc-grid">
      {evidence.map((e, i) => (
        <Reveal i={i} key={e.id}>
          <div className="doc panel" style={{ ['--c' as string]: categoryColor(e.category) }}>
            <span className="doc-strip" />
            <div className="doc-lines" aria-hidden="true">
              <i style={{ width: '70%' }} />
              <i style={{ width: '45%' }} />
              <i style={{ width: '82%' }} />
              <i style={{ width: '38%' }} />
            </div>
            <div className="doc-cat label">{humanize(e.category)}</div>
            <div className="doc-name" title={e.original_filename}>
              {e.original_filename}
            </div>
            <div className="doc-foot">
              <span className="label">
                {formatSize(e.size_bytes)} · {new Date(e.uploaded_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
              </span>
              <button
                className="btn-danger"
                onClick={() => {
                  sfx.click()
                  onDelete(e.id)
                }}
                type="button"
              >
                Remove
              </button>
            </div>
          </div>
        </Reveal>
      ))}
    </div>
  )
}
