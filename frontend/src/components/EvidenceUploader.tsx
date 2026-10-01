import { useState } from 'react'

interface EvidenceUploaderProps {
  categories: string[]
  onUpload: (file: File, category: string) => Promise<void>
}

export function EvidenceUploader({ categories, onUpload }: EvidenceUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [category, setCategory] = useState(categories[0] ?? 'other')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      await onUpload(file, category)
      setFile(null)
      const input = document.getElementById('evidence-file-input') as HTMLInputElement | null
      if (input) input.value = ''
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="form-row" onSubmit={handleSubmit}>
      <input
        id="evidence-file-input"
        type="file"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />
      <select value={category} onChange={(e) => setCategory(e.target.value)}>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c.replaceAll('_', ' ')}
          </option>
        ))}
      </select>
      <button className="btn" type="submit" disabled={!file || busy}>
        {busy ? 'Uploading…' : 'Attach evidence'}
      </button>
      {error && <span style={{ color: 'var(--warn)', fontSize: 12.5 }}>{error}</span>}
    </form>
  )
}
