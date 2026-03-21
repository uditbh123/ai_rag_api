import { useState, useRef } from 'react'
// useRef → gives us a reference to a real DOM element
// We need it to trigger the hidden file input when the user clicks the drop zone
import './Sidebar.css'

export default function Sidebar({ documents, onUpload, onDelete }) {
  // Props from App.jsx:
  //   documents → array of { source, chunk_count, preview }
  //   onUpload  → function(file) that calls App's uploadFile()
  //   onDelete  → function(sourceName) that calls App's deleteDocument()

  const [isDragging,    setIsDragging]    = useState(false)
  // true while user is dragging a file over the drop zone
  // drives the visual highlight on the drop zone

  const [uploadStatus, setUploadStatus]  = useState(null)
  // null     = idle
  // 'uploading' = in progress
  // { success: true,  message: '...' }
  // { success: false, message: '...' }

  const fileInputRef = useRef(null)
  // useRef creates a persistent reference that doesn't trigger re-renders
  // fileInputRef.current will point to the <input type="file"> DOM element
  // We use it to programmatically click the hidden input

  // ── DRAG AND DROP HANDLERS ───────────────────────────────

  function handleDragOver(e) {
    e.preventDefault()
    // preventDefault() stops the browser's default behavior
    // which is to open the file — we want to handle it ourselves
    setIsDragging(true)
  }

  function handleDragLeave() {
    setIsDragging(false)
  }

  async function handleDrop(e) {
    e.preventDefault()
    setIsDragging(false)

    // e.dataTransfer.files is a FileList — like an array of File objects
    const file = e.dataTransfer.files[0]
    // [0] = first file only. We don't support multi-file upload yet.

    if (file) await processUpload(file)
  }

  // ── FILE INPUT (click to browse) ─────────────────────────

  function handleInputChange(e) {
    const file = e.target.files[0]
    if (file) processUpload(file)
  }

  // ── SHARED UPLOAD LOGIC ──────────────────────────────────

  async function processUpload(file) {
    setUploadStatus('uploading')

    const result = await onUpload(file)
    // onUpload is the function passed from App.jsx
    // It returns { success: true/false, message: '...' }

    setUploadStatus(result)

    // Auto-clear the status message after 4 seconds
    setTimeout(() => setUploadStatus(null), 4000)
  }

  // ── RENDER ───────────────────────────────────────────────

  return (
    <aside className="sidebar">

      {/* ── UPLOAD SECTION ── */}
      <div className="sidebar-section">
        <p className="sidebar-label">Upload documents</p>

        {/* Hidden file input — triggered by clicking the drop zone */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleInputChange}
          accept=".txt,.md,.csv,.json,.py"
          style={{ display: 'none' }}
          // display:none hides it — the drop zone acts as the visual trigger
        />

        {/* Drop zone — the visible upload area */}
        <div
          className={`drop-zone ${isDragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
          // .click() programmatically opens the file picker
        >
          <div className="drop-icon">↑</div>
          <p className="drop-text">
            {isDragging ? 'Drop to upload' : 'Click or drag a file here'}
          </p>
          <p className="drop-hint">.txt · .md · .csv · .json · .py · max 10MB</p>
        </div>

        {/* Upload status feedback */}
        {uploadStatus === 'uploading' && (
          <div className="upload-status uploading">Uploading...</div>
        )}
        {uploadStatus && uploadStatus !== 'uploading' && (
          <div className={`upload-status ${uploadStatus.success ? 'success' : 'error'}`}>
            {uploadStatus.message}
          </div>
        )}
        {/* The && pattern: condition && <JSX> renders the JSX only if condition is true
            This is React's way of doing conditional rendering inline */}
      </div>

      {/* ── DOCUMENTS SECTION ── */}
      <div className="sidebar-section sidebar-docs">
        <p className="sidebar-label">Indexed documents ({documents.length})</p>

        {documents.length === 0 ? (
          <p className="empty-state">No documents yet. Upload one above.</p>
        ) : (
          <ul className="doc-list">
            {documents.map(doc => (
              // .map() renders one <li> per document
              // key= is required by React — helps it track which items changed
              // Use a unique, stable value — never use array index as key
              <li key={doc.source} className="doc-item">
                <div className="doc-info">
                  <span className="doc-name">{doc.source}</span>
                  <span className="doc-meta">{doc.chunk_count} chunk{doc.chunk_count !== 1 ? 's' : ''}</span>
                </div>
                <button
                  className="doc-delete"
                  onClick={() => onDelete(doc.source)}
                  title="Remove from knowledge base"
                >
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* ── SETTINGS SECTION ── */}
      <div className="sidebar-section sidebar-settings">
        <p className="sidebar-label">Info</p>
        <p className="settings-hint">
          Documents are split into 500-character chunks with 50-character overlap for accurate retrieval.
        </p>
      </div>

    </aside>
  )
}