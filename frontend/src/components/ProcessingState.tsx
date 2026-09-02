import { useEffect, useState } from 'react'

const STAGES = [
  { label: 'Reading document text…', duration: 2500 },
  { label: 'Highlighting buzzwords & fluff…', duration: 3000 },
  { label: 'Calculating scoring band…', duration: 3500 },
  { label: 'Drafting brutally honest feedback…', duration: 4000 },
  { label: 'Applying the verdict stamp…', duration: 5000 },
  { label: 'Finalizing review on the desk…', duration: 8000 },
  { label: 'Almost done — grading in final stage…', duration: 15000 },
]

export default function ProcessingState() {
  const [currentStageIdx, setCurrentStageIdx] = useState(0)
  const [progressPercent, setProgressPercent] = useState(12)

  useEffect(() => {
    // Stage cycle
    const stageTimer = setInterval(() => {
      setCurrentStageIdx((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev))
    }, 3200)

    // Progress bar estimation over ~15 seconds, smoothly slows down near 95% if on slow network
    const start = Date.now()
    const targetDuration = 16000

    const progressTimer = setInterval(() => {
      const elapsed = Date.now() - start
      if (elapsed < targetDuration) {
        const pct = Math.min(90, Math.round((elapsed / targetDuration) * 90) + 10)
        setProgressPercent(pct)
      } else {
        // Slow crawl while waiting for backend
        setProgressPercent((prev) => (prev < 96 ? prev + 1 : 96))
      }
    }, 250)

    return () => {
      clearInterval(stageTimer)
      clearInterval(progressTimer)
    }
  }, [])

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full bg-bg border border-white/[0.08] rounded-sm p-6 flex flex-col gap-4 text-left select-none"
    >
      {/* Single-line status in IBM Plex Mono */}
      <div className="flex items-center justify-between text-xs font-mono">
        <span className="text-paper tracking-wide">
          {STAGES[currentStageIdx]?.label || 'Grading resume…'}
        </span>
        <span className="text-tan-dim font-medium">{progressPercent}%</span>
      </div>

      {/* Thin 2px progress indicator in --stamp */}
      <div className="w-full h-[2px] bg-white/[0.08] rounded-none overflow-hidden relative">
        <div
          className="h-full bg-stamp transition-all duration-300 ease-out"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      <p className="font-mono text-[11px] text-tan-dim">
        Processing document on the grading desk · Estimated time ~15 seconds
      </p>
    </div>
  )
}
