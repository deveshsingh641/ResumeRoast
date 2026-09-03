import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App'

if (import.meta.env.VITE_API_URL) {
  axios.defaults.baseURL = import.meta.env.VITE_API_URL
}

// Automatically attach authenticated / verified user email to API requests for Pro gating
axios.interceptors.request.use((config) => {
  try {
    const userEmail = localStorage.getItem('resumeroast_user_email')
    if (userEmail) {
      config.headers = config.headers || {}
      config.headers['X-User-Email'] = userEmail
    }
  } catch {}
  return config
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
