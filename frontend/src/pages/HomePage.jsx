import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'

function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status}`}>
      <span className="badge-dot" />
      {status}
    </span>
  )
}

function formatDate(iso) {
  return new Date(iso).toLocaleString()
}

export default function HomePage() {
  const [talks, setTalks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  const fetchTalks = async () => {
    try {
      const res = await fetch('/api/talks/')
      if (!res.ok) throw new Error('Failed to load talks')
      setTalks(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTalks()
    // Poll for status updates every 5 seconds
    const interval = setInterval(fetchTalks, 5000)
    return () => clearInterval(interval)
  }, [])

  const deleteTalk = async (e, id) => {
    e.stopPropagation()
    if (!confirm('Delete this talk?')) return
    await fetch(`/api/talks/${id}`, { method: 'DELETE' })
    setTalks(prev => prev.filter(t => t.id !== id))
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>🎙️ Conversational Podcast</h1>
        <Link to="/talks/new" className="btn btn-primary" style={{ marginLeft: 'auto' }}>
          + New Talk
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {loading ? (
        <div className="loading-overlay">
          <div className="spinner" />
          <span>Loading talks…</span>
        </div>
      ) : talks.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="icon">🎧</div>
            <p>No talks yet. Create your first AI-powered podcast!</p>
            <Link to="/talks/new" className="btn btn-primary">Create a Talk</Link>
          </div>
        </div>
      ) : (
        <div className="talk-list">
          {talks.map(talk => (
            <div
              key={talk.id}
              className="talk-card"
              onClick={() => navigate(`/talks/${talk.id}`)}
            >
              <div className="talk-card-info">
                <div className="talk-card-title">{talk.title}</div>
                <div className="talk-card-date">{formatDate(talk.created_at)}</div>
              </div>
              <div className="talk-card-actions">
                <StatusBadge status={talk.status} />
                <button
                  className="btn btn-danger btn-sm"
                  onClick={e => deleteTalk(e, talk.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
