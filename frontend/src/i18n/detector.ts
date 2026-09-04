import axios from 'axios'
import i18n from 'i18next'

export const STORAGE_KEY = 'preferred_language'
export const DEFAULT_LANG = 'en'
export const HINGLISH_LANG = 'hi-IN'

export type SupportedLanguage = 'en' | 'hi-IN'

/**
 * Reads cookie by name safely in the browser.
 */
function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop()?.split(';').shift() || null
  return null
}

/**
 * Sets persistent cookie across browser sessions.
 */
function setCookie(name: string, val: string, days: number = 365): void {
  if (typeof document === 'undefined') return
  const maxAge = days * 24 * 60 * 60
  document.cookie = `${name}=${val}; path=/; max-age=${maxAge}; SameSite=Lax`
}

/**
 * Normalizes any language alias to either 'en' or 'hi-IN'.
 */
export function normalizeLang(raw?: string | null): SupportedLanguage {
  if (!raw) return DEFAULT_LANG
  const trimmed = raw.trim()
  if (trimmed === HINGLISH_LANG) return HINGLISH_LANG
  const lower = trimmed.toLowerCase()
  if (lower === 'hi' || lower === 'hi-in' || lower === 'hi_in' || lower.startsWith('hi')) {
    return HINGLISH_LANG
  }
  return DEFAULT_LANG
}

/**
 * Gets the current active language code from localStorage or cookie.
 */
export function getSavedLanguage(): SupportedLanguage | null {
  try {
    const local = localStorage.getItem(STORAGE_KEY)
    if (local) return normalizeLang(local)
    const cookie = getCookie(STORAGE_KEY)
    if (cookie) return normalizeLang(cookie)
  } catch {
    // Local storage or cookie access restricted
  }
  return null
}

/**
 * Auto-detects country on first visit via backend endpoint (/api/i18n/detect).
 * Never overrides an existing manual choice. Falls back silently to 'en'.
 */
export async function detectInitialLanguage(): Promise<SupportedLanguage> {
  const existing = getSavedLanguage()
  if (existing) {
    return existing
  }

  try {
    const res = await axios.get('/api/i18n/detect', { timeout: 3000 })
    if (res.data && res.data.language) {
      const detected = normalizeLang(res.data.language)
      // Save detected language as initial preference
      setCookie(STORAGE_KEY, detected)
      try {
        localStorage.setItem(STORAGE_KEY, detected)
      } catch {}
      return detected
    }
  } catch {
    // Silent fallback on network error or timeout
  }

  return DEFAULT_LANG
}

/**
 * Sets and permanently saves the user's manual language choice across
 * localStorage, cookie, and DB (if logged in / email available).
 */
export async function setLanguagePreference(
  lang: string,
  userEmail?: string | null
): Promise<SupportedLanguage> {
  const normalized = normalizeLang(lang)

  // 1. Update React i18next
  if (i18n.isInitialized) {
    await i18n.changeLanguage(normalized)
  }

  // 2. Persist in cookie & localStorage
  try {
    localStorage.setItem(STORAGE_KEY, normalized)
    setCookie(STORAGE_KEY, normalized)
  } catch {}

  // 3. Persist in DB if user email exists
  const email = userEmail || (() => {
    try {
      return localStorage.getItem('resumeroast_user_email')
    } catch {
      return null
    }
  })()

  if (email) {
    try {
      await axios.post('/api/user/language', {
        email: email.trim().toLowerCase(),
        language: normalized,
      })
    } catch {
      // Non-blocking sync failure
    }
  }

  // 4. Dispatch custom event for reactive UI updates
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('resumeroast:language_changed', {
        detail: { language: normalized },
      })
    )
  }

  return normalized
}
