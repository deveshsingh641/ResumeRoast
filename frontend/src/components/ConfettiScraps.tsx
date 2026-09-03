import React, { useEffect, useRef } from 'react'

interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  width: number
  height: number
  rotation: number
  vRot: number
  color: string
  opacity: number
}

const PALETTE = [
  '#E8422D', // --stamp
  '#FFB93C', // --ember
  '#7FA65C', // --success
  '#F5EFE0', // --paper
  '#C2B8A3', // --tan
]

interface ConfettiScrapsProps {
  onComplete?: () => void
}

export default function ConfettiScraps({ onComplete }: ConfettiScrapsProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    const startTime = performance.now()
    const duration = 2200 // 2.2 seconds

    // Set canvas dimensions
    const width = (canvas.width = window.innerWidth)
    const height = (canvas.height = window.innerHeight)

    // Center spawn origin behind stamp
    const originX = width / 2
    const originY = height * 0.28

    const particleCount = 65
    const particles: Particle[] = []

    for (let i = 0; i < particleCount; i++) {
      const angle = (Math.PI * 2 * i) / particleCount + (Math.random() - 0.5)
      const speed = Math.random() * 8 + 4
      particles.push({
        x: originX + (Math.random() - 0.5) * 60,
        y: originY + (Math.random() - 0.5) * 40,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed * 0.75 - Math.random() * 6 - 3, // Initial upward burst
        width: Math.random() * 10 + 6, // Rectangular paper scrap
        height: Math.random() * 6 + 3,
        rotation: Math.random() * Math.PI * 2,
        vRot: (Math.random() - 0.5) * 0.2,
        color: PALETTE[Math.floor(Math.random() * PALETTE.length)],
        opacity: 1,
      })
    }

    const gravity = 0.28
    const drag = 0.98

    const render = (currentTime: number) => {
      const elapsed = currentTime - startTime
      const progress = elapsed / duration

      if (progress >= 1) {
        ctx.clearRect(0, 0, width, height)
        if (onComplete) onComplete()
        return
      }

      ctx.clearRect(0, 0, width, height)

      for (const p of particles) {
        p.vy += gravity
        p.vx *= drag
        p.vy *= drag
        p.x += p.vx
        p.y += p.vy
        p.rotation += p.vRot

        // Fade out in the last 35% of duration
        if (progress > 0.65) {
          p.opacity = Math.max(0, 1 - (progress - 0.65) / 0.35)
        }

        ctx.save()
        ctx.translate(p.x, p.y)
        ctx.rotate(p.rotation)
        ctx.globalAlpha = p.opacity
        ctx.fillStyle = p.color

        // Draw torn paper rectangular scrap
        ctx.fillRect(-p.width / 2, -p.height / 2, p.width, p.height)
        ctx.restore()
      }

      animationFrameId = requestAnimationFrame(render)
    }

    animationFrameId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animationFrameId)
    }
  }, [onComplete])

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-50"
      style={{ width: '100vw', height: '100vh' }}
      aria-hidden="true"
    />
  )
}
