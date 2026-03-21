import { StrictMode } from "react";
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

// document.getElementById('root') finds the <div id="root"> in index.html
// createRoot() tells React "this div is yours, render inside it"
// StrictMode helps catch bugs during development — runs everything twice
// to warn if something breaks. Harmless in production.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)