import { useEffect, useState, useId } from 'react'
import type { ScoreBand } from '@/store/useAppStore'

interface ScoreStampProps {
  score: number
  band?: ScoreBand
  animate?: boolean
  size?: 'sm' | 'md' | 'lg'
  rotation?: number // e.g. -8 to -16 deg
}

export const BAND_CONFIG: Record<ScoreBand, { color: string; label: string }> = {
  weak:   { color: '#E8422D', label: 'KAMZOR' },
  mid:    { color: '#FFB93C', label: 'THIK-THAK' },
  strong: { color: '#7FA65C', label: 'DAMDAAR' },
}

export function getBandFromScore(score: number): ScoreBand {
  if (score <= 40) return 'weak'
  if (score <= 70) return 'mid'
  return 'strong'
}

const SIZE_CONFIG = {
  sm: {
    diameter: 96,
    borderWidth: 4,
    numClass: 'text-xl leading-tight',
    labelClass: 'text-xs',
    labelMargin: 'mt-0',
  },
  md: {
    diameter: 136,
    borderWidth: 5,
    numClass: 'text-2xl leading-tight',
    labelClass: 'text-xs',
    labelMargin: 'mt-1',
  },
  lg: {
    diameter: 180,
    borderWidth: 5,
    numClass: 'text-3xl leading-tight',
    labelClass: 'text-sm',
    labelMargin: 'mt-1',
  },
}

export default function ScoreStamp({
  score,
  band,
  animate = true,
  size = 'lg',
  rotation,
}: ScoreStampProps) {
  const [hasAnimated, setHasAnimated] = useState(!animate)
  const compId = useId()

  // Pick deterministic rotation between -8deg and -16deg based on score / id if not explicitly passed
  const effectiveRotation = rotation ?? (
    -8 - (Math.abs((score * 7 + compId.charCodeAt(0)) % 9))
  )

  const resolvedBand = band || getBandFromScore(score)
  const { color, label } = BAND_CONFIG[resolvedBand]
  const { diameter, borderWidth, numClass, labelClass, labelMargin } = SIZE_CONFIG[size]

  useEffect(() => {
    if (animate) {
      const timer = setTimeout(() => {
        setHasAnimated(true)
      }, 50)
      return () => clearTimeout(timer)
    }
  }, [animate])

  return (
    <div
      role="img"
      aria-label={`Score stamp: ${score} out of 100 — ${label}`}
      className={`relative inline-flex flex-col items-center justify-center select-none rounded-full shrink-0 ${
        animate && hasAnimated ? 'animate-stamp-slam' : ''
      }`}
      style={{
        width: diameter,
        height: diameter,
        border: `${borderWidth}px solid ${color}`,
        color: color,
        opacity: !animate || hasAnimated ? 1 : 0,
        transform: !animate || hasAnimated ? `rotate(${effectiveRotation}deg)` : `scale(2.2) rotate(${effectiveRotation}deg)`,
        ['--stamp-rotate' as string]: `${effectiveRotation}deg`,
        boxShadow: 'inset 0 0 0 2px rgba(23, 20, 15, 0.4)',
      }}
    >
      {/* Score number */}
      <span
        className={`font-display ${numClass} tracking-tight select-none`}
        style={{ color }}
      >
        {score}
      </span>

      {/* Uppercase band label */}
      <span
        className={`font-mono ${labelClass} uppercase font-semibold ${labelMargin}`}
        style={{ color, letterSpacing: '1px' }}
      >
        {label}
      </span>
    </div>
  )
}
