import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import InteractionPanel from '../components/InteractionPanel'
import PodcastPlayer from '../components/PodcastPlayer'

function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status}`}>
      <span className="badge-dot" />
      {status}
    </span>
  )
}

export default function TalkPage() {
  const { id } = useParams()
  const [talk, setTalk] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentSegmentIndex, setCurrentSegmentIndex] = useState(0)
  const [interactions, setInteractions] = useState([])
  const pollingRef = useRef(null)

  const fetchTalk = useCallback(async () => {
    try {
      const res = await fetch(`/api/talks/${id}`)
      if (!res.ok) throw new Error('Talk not found')
      const data = await res.json()
      setTalk(data)
      setInteractions(data.interactions || [])

      // Stop polling once ready or errored
      if (data.status === 'ready' || data.status === 'error') {
        clearInterval(pollingRef.current)
      }
    } catch (e) {
      setError(e.message)
      clearInterval(pollingRef.current)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchTalk()
    pollingRef.current = setInterval(fetchTalk, 4000)
    return () => clearInterval(pollingRef.current)
  }, [fetchTalk])

  const handleInterject = useCallback((segmentIdx) => {
    setCurrentSegmentIndex(segmentIdx)
  }, [])

  const handleNewInteraction = useCallback((interaction) => {
    setInteractions(prev => [...prev, interaction])
  }, [])

  if (loading) {
    return (
      <div className="page">
        <div className="loading-overlay">
          <div className="spinner" />
          <span>Loading talk…</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="alert alert-error">{error}</div>
        <Link to="/" className="btn btn-secondary">← Home</Link>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-header">
        <Link to="/" className="back-btn">← Back</Link>
        <h1>{talk.title}</h1>
        <StatusBadge status={talk.status} />
      </div>

      {talk.status === 'processing' && (
        <div className="alert alert-warn" style={{ marginBottom: 20 }}>
          <span className="spinner" style={{ width: 14, height: 14, marginRight: 8 }} />
          Generating script and audio… this may take a minute.
        </div>
      )}

      {talk.status === 'error' && (
        <div className="alert alert-error" style={{ marginBottom: 20 }}>
          ❌ Something went wrong during generation. Please try creating a new talk.
        </div>
      )}

      {talk.status === 'ready' && talk.segments?.length > 0 && (
        <>
          <div className="card" style={{ marginBottom: 16 }}>
            <PodcastPlayer
              segments={talk.segments}
              talkId={id}
              onInterject={handleInterject}
              interactions={interactions}
            />
          </div>

          <div className="card">
            <InteractionPanel
              talkId={id}
              currentSegmentIndex={currentSegmentIndex}
              interactions={interactions}
              onNewInteraction={handleNewInteraction}
            />
          </div>
        </>
      )}

      {talk.status === 'ready' && (!talk.segments || talk.segments.length === 0) && (
        <div className="alert alert-warn">
          Talk is ready but no segments were generated. The source material may have been empty.
        </div>
      )}
    </div>
  )
}
