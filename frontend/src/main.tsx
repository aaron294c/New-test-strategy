import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// CRITICAL: Initialize deterministic RNG with fixed seed BEFORE any calculations
import { initializeGlobalRNG } from './utils/deterministicRNG';
initializeGlobalRNG(42);  // Same seed as backend for reproducibility

console.log('✓ Deterministic RNG initialized with seed=42');

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
