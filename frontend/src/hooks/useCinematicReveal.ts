import { useState, useEffect, useRef, useCallback } from 'react'
import { playPaperRustle, playStampThud, playConfettiPop } from '@/utils/soundEffects'

interface UseCinematicRevealOptions {
  score: number
  enabled?: boolean
  onComplete?: () => void
}

export function useCinematicReveal({
  score,
  enabled = true,
  onComplete,
}: UseCinematicRevealOptions) {
  // Check prefers-reduced-motion
  const prefersReduced =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const shouldAnimate = enabled && !prefersReduced

  const [paperSettled, setPaperSettled] = useState(!shouldAnimate)
  const [markStep, setMarkStep] = useState(shouldAnimate ? 0 : 3)
  const [stampVisible, setStampVisible] = useState(!shouldAnimate)
  const [showConfetti, setShowConfetti] = useState(false)
  const [isCompleted, setIsCompleted] = useState(!shouldAnimate)

  const timersRef = useRef<number[]>([])

  const clearAllTimers = useCallback(() => {
    timersRef.current.forEach((t) => clearTimeout(t))
    timersRef.current = []
  }, [])

  const skip = useCallback(() => {
    clearAllTimers()
    setPaperSettled(true)
    setMarkStep(3)
    setStampVisible(true)
    setIsCompleted(true)
    if (score >= 70) {
      setShowConfetti(true)
    }
    if (onComplete) {
      onComplete()
    }
  }, [clearAllTimers, onComplete, score])

  useEffect(() => {
    if (!shouldAnimate) {
      setIsCompleted(true)
      if (score >= 70) {
        setShowConfetti(true)
      }
      return
    }

    clearAllTimers()

    // Explicit Centralized Timeline Array: [delayInMs, actionCallback]
    const timeline: Array<{ delay: number; run: () => void }> = [
      // 1. Paper mockup settles onto desk
      {
        delay: 50,
        run: () => {
          setPaperSettled(true)
          playPaperRustle()
        },
      },
      // 2. Pause (350ms) - intentional breath before marks start
      // 3. Sequential red pen annotations draw on
      {
        delay: 750,
        run: () => setMarkStep(1),
      },
      {
        delay: 1250,
        run: () => setMarkStep(2),
      },
      {
        delay: 1750,
        run: () => setMarkStep(3),
      },
      // 4. Another short pause (400ms)
      // 5. Stamp slams down + sound
      {
        delay: 2450,
        run: () => {
          setStampVisible(true)
          playStampThud()
        },
      },
      // 6. Confetti burst for high scores (70+) immediately after stamp settles
      {
        delay: 3000,
        run: () => {
          if (score >= 70) {
            setShowConfetti(true)
            playConfettiPop()
          }
        },
      },
      // 7. Reveal completed
      {
        delay: 3500,
        run: () => {
          setIsCompleted(true)
          if (onComplete) onComplete()
        },
      },
    ]

    // Schedule all timeline steps
    timeline.forEach(({ delay, run }) => {
      const timer = window.setTimeout(run, delay)
      timersRef.current.push(timer)
    })

    return () => {
      clearAllTimers()
    }
  }, [shouldAnimate, score, onComplete, clearAllTimers])

  // Global click/tap or keydown to skip while sequence is running
  useEffect(() => {
    if (isCompleted || !shouldAnimate) return

    const handleSkipEvent = (e: MouseEvent | KeyboardEvent | TouchEvent) => {
      // Don't intercept clicks inside buttons or links
      const target = e.target as HTMLElement | null
      if (target && (target.closest('button') || target.closest('a') || target.closest('input'))) {
        return
      }
      skip()
    }

    window.addEventListener('click', handleSkipEvent)
    window.addEventListener('keydown', handleSkipEvent)
    window.addEventListener('touchstart', handleSkipEvent, { passive: true })

    return () => {
      window.removeEventListener('click', handleSkipEvent)
      window.removeEventListener('keydown', handleSkipEvent)
      window.removeEventListener('touchstart', handleSkipEvent)
    }
  }, [isCompleted, shouldAnimate, skip])

  return {
    paperSettled,
    markStep,
    stampVisible,
    showConfetti,
    setShowConfetti,
    isCompleted,
    canSkip: !isCompleted && shouldAnimate,
    skip,
  }
}
