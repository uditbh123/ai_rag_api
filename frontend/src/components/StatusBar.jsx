// StatusBar sits at the bottom of the screen
// It receives "health" and "docCount" as props from App.jsx
// Props are read-only — this component never changes them, just displays them
import './StatusBar.css'
export default function StatusBar({ health, docCount }) {

  // Derive display values from the health object
  // health is null on first render (before the fetch completes)
  // so we always provide fallback values with || and ?.

  const isOnline  = health?.status === 'ok'
  // ?. is "optional chaining" — health?.status means:
  // "if health exists, read .status — otherwise return undefined (not an error)"
  // Without it, health.status when health=null would crash with TypeError

  const modelName = health?.available_models?.[0] || 'no model'
  // available_models is an array like ["tinyllama:latest"]
  // [0] gets the first one
  // || 'no model' is the fallback if the array is empty

  const chunks    = health?.docs_indexed ?? 0
  // ?? is "nullish coalescing" — like || but only falls back on null/undefined
  // (not on 0 or false, which || would also treat as falsy)

  return (
    <div className="status-bar">

      {/* Connection status dot + label */}
      <div className="status-item">
        <span className={`status-dot ${isOnline ? 'online' : 'offline'}`} />
        {/* Template literal className — adds "online" or "offline" class
            based on the boolean. This drives the green/red dot color in CSS */}
        <span>{isOnline ? 'Backend online' : 'Backend offline'}</span>
      </div>

      <div className="status-item">
        <span>Model: {modelName}</span>
      </div>

      <div className="status-item">
        <span>{chunks} chunks indexed</span>
      </div>

      <div className="status-item">
        <span>{docCount} document{docCount !== 1 ? 's' : ''}</span>
        {/* Pluralization: "1 document" vs "3 documents" */}
      </div>

      <div className="status-item status-right">
        <span>Streaming via SSE</span>
      </div>

    </div>
  )
}