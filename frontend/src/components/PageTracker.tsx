import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

/**
 * First-party, ad-blocker proof visitor & pageview tracker.
 * Dispatches a lightweight asynchronous beacon to /api/track without blocking UI.
 */
export function PageTracker() {
  const location = useLocation()

  useEffect(() => {
    try {
      const apiBase = import.meta.env.VITE_API_URL || ''
      const trackUrl = `${apiBase}/api/track`
      const payload = JSON.stringify({
        path: location.pathname,
        referrer: document.referrer || undefined,
      })

      // Use navigator.sendBeacon for non-blocking asynchronous transmission
      if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' })
        navigator.sendBeacon(trackUrl, blob)
      } else {
        fetch(trackUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
          keepalive: true,
        }).catch(() => {})
      }
    } catch {}
  }, [location.pathname])

  return null
}
