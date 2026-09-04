import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import enTranslation from './locales/en.json'
import hiTranslation from './locales/hi.json'
import {
  DEFAULT_LANG,
  HINGLISH_LANG,
  getSavedLanguage,
  detectInitialLanguage,
  normalizeLang,
} from './detector'

const resources = {
  en: { translation: enTranslation },
  'hi-IN': { translation: hiTranslation },
  hi: { translation: hiTranslation },
}

// Check if user already made an explicit choice, otherwise default to 'en'
// while async background detection runs
const initialLang = getSavedLanguage() || DEFAULT_LANG

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: initialLang,
    fallbackLng: DEFAULT_LANG,
    supportedLngs: ['en', 'hi-IN', 'hi'],
    interpolation: {
      escapeValue: false, // React already safe from XSS
    },
  })

// If no manual preference was stored yet, auto-detect country asynchronously
if (typeof window !== 'undefined' && !getSavedLanguage()) {
  detectInitialLanguage().then((detected) => {
    if (detected && detected !== i18n.language) {
      i18n.changeLanguage(detected)
    }
  })
}

export function getCurrentLanguage(): string {
  return normalizeLang(i18n.language)
}

export default i18n
