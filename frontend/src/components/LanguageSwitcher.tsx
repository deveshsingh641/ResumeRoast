import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  SupportedLanguage,
  normalizeLang,
  setLanguagePreference,
} from '@/i18n/detector'
import { playPaperRustle } from '@/utils/soundEffects'

interface LanguageSwitcherProps {
  className?: string
  compact?: boolean
}

export default function LanguageSwitcher({
  className = '',
  compact = false,
}: LanguageSwitcherProps) {
  const { i18n } = useTranslation()
  const [currentLang, setCurrentLang] = useState<SupportedLanguage>(() =>
    normalizeLang(i18n.language)
  )

  useEffect(() => {
    const handleLanguageChange = (lng: string) => {
      setCurrentLang(normalizeLang(lng))
    }

    i18n.on('languageChanged', handleLanguageChange)

    const handleCustomEvent = (e: Event) => {
      const custom = e as CustomEvent<{ language: string }>
      if (custom.detail?.language) {
        setCurrentLang(normalizeLang(custom.detail.language))
      }
    }

    window.addEventListener('resumeroast:language_changed', handleCustomEvent)

    return () => {
      i18n.off('languageChanged', handleLanguageChange)
      window.removeEventListener('resumeroast:language_changed', handleCustomEvent)
    }
  }, [i18n])

  const handleSelect = async (lang: SupportedLanguage) => {
    if (lang === currentLang) return
    playPaperRustle()
    setCurrentLang(lang)
    await setLanguagePreference(lang)
  }

  return (
    <div
      role="group"
      aria-label="Language selector"
      className={`inline-flex items-center p-0.5 rounded-md border border-white/[0.1] bg-surface-card/60 backdrop-blur-md select-none transition-all ${className}`}
    >
      {/* English Option */}
      <button
        type="button"
        onClick={() => handleSelect('en')}
        aria-pressed={currentLang === 'en'}
        title="Switch to English UI and Roast Persona"
        className={`px-2 py-1 rounded text-xs font-mono font-medium transition-all duration-200 flex items-center gap-1 ${
          currentLang === 'en'
            ? 'bg-flame-500/20 text-flame-400 shadow-sm border border-flame-500/30'
            : 'text-tan-muted hover:text-tan hover:bg-white/[0.04] border border-transparent'
        }`}
      >
        <span className="font-semibold tracking-wide">EN</span>
        {!compact && (
          <span className="text-[10px] opacity-70 hidden sm:inline">English</span>
        )}
      </button>

      {/* Divider */}
      <div className="w-[1px] h-3 bg-white/[0.1] mx-0.5" aria-hidden="true" />

      {/* Hinglish Option */}
      <button
        type="button"
        onClick={() => handleSelect('hi-IN')}
        aria-pressed={currentLang === 'hi-IN'}
        title="Switch to Hinglish WhatsApp-Style UI and Roast Persona"
        className={`px-2 py-1 rounded text-xs font-mono font-medium transition-all duration-200 flex items-center gap-1 ${
          currentLang === 'hi-IN'
            ? 'bg-flame-500/20 text-flame-400 shadow-sm border border-flame-500/30'
            : 'text-tan-muted hover:text-tan hover:bg-white/[0.04] border border-transparent'
        }`}
      >
        <span className="font-semibold tracking-wide">हिं</span>
        {!compact && (
          <span className="text-[10px] opacity-70 hidden sm:inline">Hinglish</span>
        )}
      </button>
    </div>
  )
}
