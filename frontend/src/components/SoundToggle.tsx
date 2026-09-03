import { useState, useEffect } from 'react'
import { isSoundEnabled, setSoundEnabled } from '@/utils/soundEffects'

interface SoundToggleProps {
  className?: string
  compact?: boolean
}

export default function SoundToggle({ className = '', compact = false }: SoundToggleProps) {
  const [enabled, setEnabled] = useState(false)

  useEffect(() => {
    setEnabled(isSoundEnabled())
  }, [])

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    const next = !enabled
    setEnabled(next)
    setSoundEnabled(next)
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      aria-label={enabled ? 'Sound effects enabled (click to mute)' : 'Sound effects muted (click to enable)'}
      title={enabled ? 'Audio effects ON — click to mute' : 'Audio effects MUTED — click to enable desk sounds'}
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm border transition-all text-xs font-mono select-none ${
        enabled
          ? 'border-amber-500/40 bg-amber-500/10 text-amber-300 hover:border-amber-400'
          : 'border-white/[0.08] bg-white/[0.02] text-tan-dim hover:text-tan hover:border-white/[0.16]'
      } ${className}`}
    >
      <span className="text-sm leading-none" aria-hidden="true">
        {enabled ? '🔊' : '🔇'}
      </span>
      {!compact && (
        <span className="tracking-wide text-[11px] uppercase">
          Sound: {enabled ? 'ON' : 'OFF'}
        </span>
      )}
    </button>
  )
}
