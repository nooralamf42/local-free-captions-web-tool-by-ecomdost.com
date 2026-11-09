import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { StoreProvider } from './store'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StoreProvider>
    <App />
  </StoreProvider>,
)
