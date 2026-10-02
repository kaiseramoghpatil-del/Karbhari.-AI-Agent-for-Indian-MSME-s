import { useRef, useState } from 'react'
import { Icon } from './Icon'
import { categoryColor, humanize } from '../lib/format'
import { sfx } from '../lib/sound'

interface EvidenceUploaderProps {
  categories: string[]
  onUpload: (file: File, category: string) => Promise<void>
}

/** Drag-and-drop dropzone with category chips. */
export function EvidenceUploader({ categories, onUpload }: EvidenceUploaderProps) {
  const [file, setFile] = useState<File | null>(null)
  const [category, setCategory] = useState(categories[0] ?? 'other')
  const [busy, setBusy] = useState(false)
  const [over, setOver] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function submit() {
    if (!file) return
    sfx.click()
    setBusy(true)
    setError(null)
    try {
      await onUpload(file, category)
      sfx.paper()
      sfx.chime()
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
    } catch (err) {
      sfx.buzz()
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="uploader">
      <div
        className={`dropzone${over ? ' over' : ''}${file ? ' has-file' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          if (!over) sfx.tick()
          setOver(true)
        }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setOver(false)
          const f = e.dataTransfer.files?.[0]
          if (f) {
            setFile(f)
            sfx.paper()
          }
        }}
        role="button"
        tabIndex={0}
      >
        <input ref={inputRef} type="file" hidden onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <div className="dz-icon">
          <Icon name={file ? 'doc' : 'upload'} size={26} />
        </div>
        {file ? (
          <>
            <div className="dz-title">{file.name}</div>
            <div className="label">{(file.size / 1024).toFixed(1)} KB · ready to attach</div>
          </>
        ) : (
          <>
            <div className="dz-title">Drop a document here, or click to browse</div>
            <div className="label">PDF · XLSX · CSV · TXT</div>
          </>
        )}
        <span className="dz-scan" />
      </div>

      <div className="dz-controls">
        <div className="cat-chips">
          {categories.map((c) => (
            <button
              key={c}
              type="button"
              className={`cat-chip${c === category ? ' active' : ''}`}
              style={{ ['--c' as string]: categoryColor(c) }}
              onClick={() => {
                setCategory(c)
                sfx.tick()
              }}
            >
              <i />
              {humanize(c)}
            </button>
          ))}
        </div>
        <button className="btn" type="button" onClick={submit} disabled={!file || busy}>
          <Icon name="upload" size={16} />
          {busy ? 'Attaching…' : 'Attach evidence'}
        </button>
      </div>
      {error && <div className="error-banner" style={{ marginTop: 10 }}>{error}</div>}
    </div>
  )
}
