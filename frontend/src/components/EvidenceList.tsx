import type { Evidence } from '../types'

interface EvidenceListProps {
  evidence: Evidence[]
  onDelete: (evidenceId: string) => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function EvidenceList({ evidence, onDelete }: EvidenceListProps) {
  if (evidence.length === 0) {
    return <div className="empty-state">No evidence attached yet.</div>
  }

  return (
    <table className="evidence-table">
      <thead>
        <tr>
          <th>File</th>
          <th>Category</th>
          <th>Size</th>
          <th>Uploaded</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {evidence.map((e) => (
          <tr key={e.id}>
            <td>{e.original_filename}</td>
            <td>
              <span className="category-tag">{e.category.replaceAll('_', ' ')}</span>
            </td>
            <td>{formatSize(e.size_bytes)}</td>
            <td>{new Date(e.uploaded_at).toLocaleString()}</td>
            <td>
              <button className="btn-danger" onClick={() => onDelete(e.id)} type="button">
                Remove
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
