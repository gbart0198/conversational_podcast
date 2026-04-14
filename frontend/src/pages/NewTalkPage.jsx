import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'

const DEFAULT_SOURCE = { type: 'text', content: '' }

export default function NewTalkPage() {
  const [title, setTitle] = useState('')
  const [sources, setSources] = useState([{ ...DEFAULT_SOURCE }])
  const [uploadMode, setUploadMode] = useState(false)
  const [file, setFile] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const addSource = () => setSources(prev => [...prev, { ...DEFAULT_SOURCE }])
  const removeSource = idx => setSources(prev => prev.filter((_, i) => i !== idx))
  const updateSource = (idx, field, value) =>
    setSources(prev => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)))

  const handleSubmit = async e => {
    e.preventDefault()
    setError(null)

    if (!title.trim()) {
      setError('Please enter a title for your talk.')
      return
    }

    setSubmitting(true)
    try {
      let res

      if (uploadMode) {
        if (!file) { setError('Please select a file.'); setSubmitting(false); return }
        const formData = new FormData()
        formData.append('title', title.trim())
        formData.append('file', file)
        res = await fetch('/api/talks/upload', { method: 'POST', body: formData })
      } else {
        const validSources = sources.filter(s => s.content.trim())
        if (!validSources.length) {
          setError('Please add at least one source.')
          setSubmitting(false)
          return
        }
        res = await fetch('/api/talks/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: title.trim(), sources: validSources }),
        })
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to create talk')
      }

      const talk = await res.json()
      navigate(`/talks/${talk.id}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/" className="back-btn">← Back</Link>
        <h1>New Talk</h1>
      </div>

      <div className="card">
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Talk Title</label>
            <input
              id="title"
              type="text"
              placeholder="e.g. Introduction to Quantum Computing"
              value={title}
              onChange={e => setTitle(e.target.value)}
              required
            />
          </div>

          {/* Source type toggle */}
          <div className="form-group">
            <label>Source Type</label>
            <div className="tabs">
              <button
                type="button"
                className={`tab ${!uploadMode ? 'active' : ''}`}
                onClick={() => setUploadMode(false)}
              >
                Text / URL
              </button>
              <button
                type="button"
                className={`tab ${uploadMode ? 'active' : ''}`}
                onClick={() => setUploadMode(true)}
              >
                Upload File (PDF / TXT)
              </button>
            </div>
          </div>

          {uploadMode ? (
            <div className="form-group">
              <label htmlFor="file">File</label>
              <input
                id="file"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={e => setFile(e.target.files[0] || null)}
              />
            </div>
          ) : (
            <div className="form-group">
              <label>Sources</label>
              <div className="source-list">
                {sources.map((src, idx) => (
                  <div key={idx} className="source-entry">
                    {sources.length > 1 && (
                      <button
                        type="button"
                        className="remove-btn"
                        onClick={() => removeSource(idx)}
                        title="Remove source"
                      >
                        ✕
                      </button>
                    )}
                    <div className="form-group" style={{ marginBottom: 10 }}>
                      <label>Type</label>
                      <select
                        value={src.type}
                        onChange={e => updateSource(idx, 'type', e.target.value)}
                      >
                        <option value="text">Plain Text</option>
                        <option value="url">URL</option>
                      </select>
                    </div>
                    <div className="form-group" style={{ marginBottom: 0 }}>
                      <label>{src.type === 'url' ? 'URL' : 'Content'}</label>
                      {src.type === 'url' ? (
                        <input
                          type="url"
                          placeholder="https://example.com/article"
                          value={src.content}
                          onChange={e => updateSource(idx, 'content', e.target.value)}
                        />
                      ) : (
                        <textarea
                          placeholder="Paste your source text here…"
                          value={src.content}
                          onChange={e => updateSource(idx, 'content', e.target.value)}
                        />
                      )}
                    </div>
                  </div>
                ))}
                <button type="button" className="add-source-btn" onClick={addSource}>
                  + Add another source
                </button>
              </div>
            </div>
          )}

          <div className="alert alert-info" style={{ marginTop: 8 }}>
            ℹ️ Script and audio generation starts immediately. You'll be redirected to your talk where you can follow the progress.
          </div>

          <button type="submit" className="btn btn-primary" disabled={submitting} style={{ width: '100%', marginTop: 8 }}>
            {submitting ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Generating…</> : '🎙️ Create Talk'}
          </button>
        </form>
      </div>
    </div>
  )
}
