import { useState, useEffect, useRef } from 'react'
import Message from './Message'
import './ChatPanel.css'

export default function ChatPanel({ messages, isStreaming, onSend }) {

  const [input, setInput]       = useState('')
  // Controlled input — React owns the value, not the DOM
  // Every keystroke updates this state → React re-renders → input shows new value

  const bottomRef = useRef(null)
  // A ref to an invisible div at the bottom of the message list
  // We call .scrollIntoView() on it to auto-scroll when new messages arrive

  // Auto-scroll whenever messages change (new message or new token appended)
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  // [messages] = dependency array — this effect re-runs every time messages changes
  // smooth = animated scroll instead of instant jump

  function handleKeyDown(e) {
    // Send on Enter, allow Shift+Enter for newlines
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()  // stop textarea from adding a newline
      handleSend()
    }
  }

  function handleSend() {
    if (!input.trim() || isStreaming) return
    onSend(input.trim())
    setInput('')           // clear the input after sending
  }

  return (
    <div className="chat-panel">

      {/* Message list */}
      <div className="messages-container">
        {messages.map((msg, index) => (
          <Message
            key={msg.id}
            message={msg}
            // Only pass isStreaming=true to the LAST AI message
            // so the cursor only appears on the currently-generating message
            isStreaming={isStreaming && index === messages.length - 1 && msg.role === 'ai'}
          />
        ))}

        {/* Invisible anchor at the bottom for auto-scroll */}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="input-row">
        <textarea
          className="chat-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          // onChange fires on every keystroke
          // e.target.value is the new full string in the textarea
          onKeyDown={handleKeyDown}
          placeholder="Ask a question about your documents... (Enter to send)"
          rows={1}
          disabled={isStreaming}
          // disabled while AI is responding — prevents double-sending
        />
        <button
          className={`send-btn ${isStreaming ? 'sending' : ''}`}
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
        >
          {isStreaming ? 'Thinking...' : 'Send'}
        </button>
      </div>

    </div>
  )
}