import './Message.css'

export default function Message({ message, isStreaming }) {
  // message = { id, role: 'user'|'ai', text, sources: [] }
  // isStreaming = true if THIS message is currently being streamed

  const isAI   = message.role === 'ai'
  const isUser = message.role === 'user'

  return (
    <div className={`message-wrapper ${isUser ? 'user-wrapper' : 'ai-wrapper'}`}>
      <div className={`message-bubble ${isUser ? 'user-bubble' : 'ai-bubble'}`}>

        {/* Message text */}
        <p className="message-text">
          {message.text}
          {/* Blinking cursor — only shown on the last AI message while streaming */}
          {isAI && isStreaming && <span className="cursor" />}
        </p>

        {/* Sources — only shown on AI messages that have sources */}
        {isAI && message.sources.length > 0 && (
          <div className="sources">
            <span className="sources-label">Sources: </span>
            {message.sources.map((src, i) => (
              <span key={i} className="source-chip">
                {src.slice(0, 80)}{src.length > 80 ? '...' : ''}
                {/* Show first 80 chars of each source chunk as a preview */}
              </span>
            ))}
          </div>
        )}

      </div>
    </div>
  )
}