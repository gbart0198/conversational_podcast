import { useRef, useState } from 'react'

export default function InteractionPanel({ talkId, currentSegmentIndex, interactions, onNewInteraction }) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recording, setRecording] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const audioRefs = useRef({})

  const handleSubmit = async e => {
    e?.preventDefault()
    if (!question.trim()) return
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`/api/talks/${talkId}/interact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), segment_index: currentSegmentIndex }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Failed to get answer')
      }
      const interaction = await res.json()
      setQuestion('')
      onNewInteraction?.(interaction)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      chunksRef.current = []
      const mr = new MediaRecorder(stream)
      mr.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        await transcribeAndAsk(blob)
      }
      mr.start()
      mediaRecorderRef.current = mr
      setRecording(true)
    } catch {
      setError('Microphone access denied or not available.')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setRecording(false)
  }

  const transcribeAndAsk = async blob => {
    setLoading(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('audio', blob, 'question.webm')
      formData.append('talk_id', talkId)
      formData.append('segment_index', String(currentSegmentIndex))

      const res = await fetch(`/api/talks/${talkId}/interact/voice`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        throw new Error(data.detail || 'Voice transcription failed')
      }
      const interaction = await res.json()
      onNewInteraction?.(interaction)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const playAnswerAudio = id => {
    const audio = audioRefs.current[id]
    if (!audio) return
    if (audio.paused) audio.play()
    else { audio.pause(); audio.currentTime = 0 }
  }

  return (
    <div className="interaction-panel">
      <h3>💬 Ask a Question</h3>

      {error && <div className="alert alert-error">{error}</div>}

      <form className="question-form" onSubmit={handleSubmit}>
        <textarea
          placeholder="Ask about anything in the podcast… (Enter to send, Shift+Enter for new line)"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={2}
          disabled={loading}
        />
        <button
          type="button"
          className={`voice-btn ${recording ? 'recording' : ''}`}
          title={recording ? 'Stop recording' : 'Ask by voice'}
          onClick={recording ? stopRecording : startRecording}
          disabled={loading}
        >
          {recording ? '⏹' : '🎤'}
        </button>
        <button type="submit" className="btn btn-primary" disabled={loading || !question.trim()}>
          {loading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Ask'}
        </button>
      </form>

      {interactions?.length > 0 && (
        <div className="interaction-history">
          {[...interactions].reverse().map(item => (
            <div key={item.id} className="interaction-entry">
              <div className="interaction-q">
                <strong>You (at segment {item.segment_index + 1}):</strong> {item.question}
              </div>
              <div className="interaction-a">{item.answer}</div>
              {item.audio_file && (
                <>
                  <audio
                    ref={el => { audioRefs.current[item.id] = el }}
                    src={`/audio/${item.audio_file}`}
                    style={{ display: 'none' }}
                  />
                  <button
                    className="btn btn-secondary btn-sm interaction-audio-btn"
                    onClick={() => playAnswerAudio(item.id)}
                  >
                    🔊 Play answer
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
