import { useEffect, useRef, useState, useCallback } from 'react'

const SPEAKER_COLORS = {
  Alex: 'speaker-Alex',
  Sam: 'speaker-Sam',
}

export default function PodcastPlayer({ segments, talkId, onInterject, interactions }) {
  const audioRef = useRef(null)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [showInterject, setShowInterject] = useState(false)
  const [finished, setFinished] = useState(false)
  const segmentListRef = useRef(null)

  // Scroll active segment into view
  useEffect(() => {
    if (!segmentListRef.current) return
    const active = segmentListRef.current.querySelector('.segment-item.active')
    if (active) active.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [currentIndex])

  const playSegment = useCallback((index) => {
    if (!segments[index]) return
    const seg = segments[index]
    if (!seg.audio_file) return

    const audio = audioRef.current
    audio.src = `/audio/${seg.audio_file}`
    audio.play().catch(() => {})
    setCurrentIndex(index)
    setIsPlaying(true)
    setIsPaused(false)
    setFinished(false)
  }, [segments])

  const handleEnded = useCallback(() => {
    const next = currentIndex + 1
    if (next < segments.length) {
      playSegment(next)
    } else {
      setIsPlaying(false)
      setFinished(true)
    }
  }, [currentIndex, segments, playSegment])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    audio.addEventListener('ended', handleEnded)
    return () => audio.removeEventListener('ended', handleEnded)
  }, [handleEnded])

  const handlePlay = () => {
    if (!segments.length || !segments[0].audio_file) return
    if (isPaused) {
      audioRef.current.play()
      setIsPlaying(true)
      setIsPaused(false)
    } else {
      playSegment(currentIndex || 0)
    }
  }

  const handlePause = () => {
    audioRef.current.pause()
    setIsPlaying(false)
    setIsPaused(true)
  }

  const handleInterjectClick = () => {
    if (isPlaying) handlePause()
    setShowInterject(true)
    onInterject?.(currentIndex)
  }

  const handleResumeAfterInterject = () => {
    setShowInterject(false)
    const next = currentIndex + 1
    if (next < segments.length) {
      playSegment(next)
    } else {
      setFinished(true)
    }
  }

  if (!segments.length) {
    return (
      <div className="alert alert-warn">
        No audio segments available yet. Please wait for generation to finish.
      </div>
    )
  }

  // Find interactions at each segment
  const interactionsBySegment = {}
  interactions?.forEach(i => {
    if (!interactionsBySegment[i.segment_index]) interactionsBySegment[i.segment_index] = []
    interactionsBySegment[i.segment_index].push(i)
  })

  return (
    <div className="player-container">
      <audio ref={audioRef} />

      {/* Segment list */}
      <div className="segment-list" ref={segmentListRef}>
        {segments.map((seg, idx) => (
          <div
            key={seg.id}
            className={[
              'segment-item',
              idx === currentIndex && isPlaying ? 'active' : '',
              idx < currentIndex ? 'played' : '',
            ].join(' ')}
          >
            <span className={`speaker-tag ${SPEAKER_COLORS[seg.speaker] || ''}`}>
              {seg.speaker}
            </span>
            <span className="segment-text">{seg.text}</span>
          </div>
        ))}
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="player-controls">
          {!isPlaying ? (
            <button className="btn btn-primary" onClick={handlePlay} disabled={finished && !isPaused}>
              {finished ? '✅ Finished' : isPaused ? '▶ Resume' : '▶ Play'}
            </button>
          ) : (
            <button className="btn btn-secondary" onClick={handlePause}>
              ⏸ Pause
            </button>
          )}

          {(isPlaying || isPaused) && (
            <button
              className="btn btn-secondary"
              onClick={handleInterjectClick}
              style={{ borderColor: 'var(--accent)', color: 'var(--accent-light)' }}
            >
              💬 Interject
            </button>
          )}

          {finished && (
            <button className="btn btn-secondary" onClick={() => { setCurrentIndex(0); setFinished(false) }}>
              ↺ Restart
            </button>
          )}

          <span className="progress-info">
            Segment {Math.min(currentIndex + 1, segments.length)} / {segments.length}
          </span>
        </div>

        {showInterject && (
          <div style={{ marginTop: 12 }}>
            <div className="alert alert-info">
              ⏸ Paused at segment {currentIndex + 1}. Ask your question below, then resume.
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => { setShowInterject(false); if (isPaused) handlePlay() }}>
              ▶ Resume without asking
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
