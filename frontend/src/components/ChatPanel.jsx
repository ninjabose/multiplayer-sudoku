import { useEffect, useRef, useState } from 'react'

export default function ChatPanel({
  messages,
  onSend,
  disabled,
  placeholder,
  error,
}) {
  const [draft, setDraft] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'end' })
  }, [messages])

  function submit(event) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || disabled) return
    onSend(text)
    setDraft('')
  }

  return (
    <section className="chat-panel">
      <div className="chat-log" role="log" aria-live="polite">
        {messages.length === 0 ? (
          <p className="muted">No messages yet.</p>
        ) : (
          messages.map((item, index) => (
            <p key={`${item.timestamp}-${index}`} className="chat-line">
              <span className="chat-time">{formatTime(item.timestamp)}</span>
              <strong>{item.username}</strong>
              <span>{item.message}</span>
            </p>
          ))
        )}
        <div ref={endRef} />
      </div>
      {error ? <p className="chat-error">{error}</p> : null}
      <form className="chat-form" onSubmit={submit}>
        <input
          value={draft}
          maxLength={200}
          disabled={disabled}
          placeholder={placeholder || 'Type a message'}
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" className="ghost" disabled={disabled}>
          Send
        </button>
      </form>
    </section>
  )
}

function formatTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
