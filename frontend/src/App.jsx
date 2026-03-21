import { useState, useEffect } from 'react'
// useState  → stores data that changes over time (messages, documents, etc.)
// useEffect → runs code when something changes (like fetching health on startup)

import StatusBar from './components/StatusBar'
import Sidebar   from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import './App.css'

export default function App() {

  // ── STATE ────────────────────────────────────────────────
  // Each useState(initialValue) gives us:
  //   [currentValue, functionToUpdateIt]
  // When we call the update function, React re-renders the component

  const [health, setHealth]       = useState(null)
  // health = null means "not checked yet"
  // health = { status: "ok", ollama: "connected", docs_indexed: 1 }

  const [documents, setDocuments] = useState([])
  // List of indexed documents from /ingest/list

  const [messages, setMessages]   = useState([
    // Start with a welcome message so the chat isn't empty
    {
      id: 1,
      role: 'ai',
      text: 'Hello! Upload a document using the sidebar, then ask me anything about it.',
      sources: []
    }
  ])

  const [isStreaming, setIsStreaming] = useState(false)
  // true while the AI is generating — used to disable the send button
  // and show a "thinking..." indicator

  // ── FETCH HEALTH ON STARTUP ──────────────────────────────
  // useEffect(fn, []) runs fn exactly once — when the component first mounts
  // The empty [] means "no dependencies — only run on mount"
  // This is how it's done "on page load" logic in React
  useEffect(() => {
    fetchHealth()
    fetchDocuments()
  }, [])

  async function fetchHealth() {
    try {
      const res  = await fetch('/api/health')
      const data = await res.json()
      setHealth(data)
    } catch {
      setHealth({ status: 'error', ollama: 'unreachable' })
    }
  }

  async function fetchDocuments() {
    try {
      const res  = await fetch('/api/ingest/list')
      const data = await res.json()
      setDocuments(data.documents || [])
    } catch {
      console.error('Could not fetch documents')
    }
  }

  // ── SEND MESSAGE WITH STREAMING ──────────────────────────
  async function sendMessage(question) {
    if (!question.trim() || isStreaming) return

    // 1. Add the user's message to the chat immediately
    const userMsg = { id: Date.now(), role: 'user', text: question, sources: [] }
    setMessages(prev => [...prev, userMsg])
    // prev → the current messages array
    // [...prev, userMsg] → spread existing + append new one
    // React needs a NEW array reference to detect the change — never mutate directly

    // 2. Add an empty AI message placeholder — we'll stream tokens into it
    const aiMsgId = Date.now() + 1
    setMessages(prev => [...prev, { id: aiMsgId, role: 'ai', text: '', sources: [] }])

    setIsStreaming(true)

    try {
      // 3. Open the SSE stream
      // fetch() with a POST and reading the body as a stream
      const response = await fetch('/api/query/stream', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ question, n_results: 3 })
      })

      // response.body is a ReadableStream — a browser API for reading
      // data as it arrives, without waiting for the whole response
      const reader  = response.body.getReader()
      // TextDecoder converts raw bytes → string
      const decoder = new TextDecoder()

      // 4. Read chunks as they stream in
      while (true) {
        const { done, value } = await reader.read()
        // done  = true when the stream ends
        // value = Uint8Array of raw bytes for this chunk

        if (done) break

        // Decode bytes → string
        const text = decoder.decode(value)

        // SSE format: each event is "data: {...json...}\n\n"
        // Split on \n\n to get individual events (multiple can arrive at once)
        const lines = text.split('\n\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          const jsonStr = line.replace('data: ', '')
          try {
            const event = JSON.parse(jsonStr)

            if (event.error) {
              // Server sent an error — show it in the message
              setMessages(prev => prev.map(m =>
                m.id === aiMsgId
                  ? { ...m, text: `Error: ${event.error}` }
                  : m
              ))
              break
            }

            if (event.sources) {
              // First event always contains sources — update the AI message
              setMessages(prev => prev.map(m =>
                m.id === aiMsgId ? { ...m, sources: event.sources } : m
              ))
            }

            if (event.token) {
              // Append the token to the AI message text
              // prev.map() creates a NEW array (required by React)
              // We find the AI message by id and append the token to its text
              setMessages(prev => prev.map(m =>
                m.id === aiMsgId
                  ? { ...m, text: m.text + event.token }
                  : m
              ))
            }

          } catch {
            // JSON parse failed — skip malformed event
          }
        }
      }

    } catch (err) {
      // Network error — update the placeholder message
      setMessages(prev => prev.map(m =>
        m.id === aiMsgId
          ? { ...m, text: 'Connection error. Is the backend running?' }
          : m
      ))
    } finally {
      // finally always runs — even if there was an error
      // This ensures isStreaming is always reset
      setIsStreaming(false)
    }
  }

  // ── HANDLE FILE UPLOAD ───────────────────────────────────
  async function uploadFile(file) {
    // FormData is the browser's way of packaging a file for multipart upload
    // It's what HTML forms use when enctype="multipart/form-data"
    const formData = new FormData()
    formData.append('file', file)
    // 'file' must match the parameter name in FastAPI: upload_file(file: UploadFile)

    try {
      const res  = await fetch('/api/ingest/upload', {
        method: 'POST',
        body:   formData
        // Don't set Content-Type header! Browser sets it automatically
        // with the correct boundary string for multipart data
      })
      const data = await res.json()

      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      // Refresh documents list and health after successful upload
      await fetchDocuments()
      await fetchHealth()

      return { success: true, message: data.message }
    } catch (err) {
      return { success: false, message: err.message }
    }
  }

  // ── HANDLE DOCUMENT DELETE ───────────────────────────────
  async function deleteDocument(sourceName) {
    try {
      await fetch(`/api/ingest/document/${encodeURIComponent(sourceName)}`, {
        method: 'DELETE'
      })
      // encodeURIComponent handles filenames with spaces or special chars
      await fetchDocuments()
      await fetchHealth()
    } catch (err) {
      console.error('Delete failed:', err)
    }
  }

  // ── RENDER ───────────────────────────────────────────────
  // Every component receives "props" — data passed from parent to child
  // Like function arguments but for UI components
  return (
    <div className="app-layout">
      <StatusBar health={health} docCount={documents.length} />

      <div className="main-content">
        <Sidebar
          documents={documents}
          onUpload={uploadFile}
          onDelete={deleteDocument}
        />
        <ChatPanel
          messages={messages}
          isStreaming={isStreaming}
          onSend={sendMessage}
        />
      </div>
    </div>
  )
}