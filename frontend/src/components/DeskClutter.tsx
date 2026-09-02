import { useEffect, useState } from 'react'

interface DeskClutterProps {
  stickyText?: string
  stickyRotation?: number
}

export default function DeskClutter({
  stickyText = 'friday se pehle fix kar le yaar!! 😭',
  stickyRotation = 4,
}: DeskClutterProps) {
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    // Detect touch devices
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
      setIsTouch(true)
      return
    }

    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window
      const x = (e.clientX / innerWidth - 0.5) * 12 // max 6px each way
      const y = (e.clientY / innerHeight - 0.5) * 12
      setOffset({ x, y })
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div
      className="pointer-events-none absolute inset-0 overflow-hidden select-none z-0"
      aria-hidden="true"
    >
      {/* ── 1. Asymmetric Coffee Ring Stain (Top-Left or Bottom-Right) ── */}
      <div
        className="absolute top-12 -left-16 sm:-left-8 opacity-25 transition-transform duration-300 ease-out"
        style={{
          transform: isTouch ? 'none' : `translate3d(${offset.x * 0.4}px, ${offset.y * 0.4}px, 0)`,
        }}
      >
        <svg width="220" height="220" viewBox="0 0 200 200" fill="none">
          {/* Outer ring with slight irregularity */}
          <circle
            cx="100"
            cy="100"
            r="82"
            stroke="#8A8168"
            strokeWidth="3.5"
            strokeDasharray="14 3 40 4 80 6"
            strokeOpacity="0.4"
          />
          {/* Inner ring */}
          <circle
            cx="98"
            cy="102"
            r="75"
            stroke="#8A8168"
            strokeWidth="2"
            strokeOpacity="0.25"
          />
          {/* Drip blotch */}
          <ellipse
            cx="170"
            cy="115"
            rx="5"
            ry="9"
            transform="rotate(25 170 115)"
            fill="#8A8168"
            fillOpacity="0.3"
          />
        </svg>
      </div>

      {/* ── 2. Crumpled / Rejected Mini Resume (Bottom-Left) ── */}
      <div
        className="absolute bottom-16 -left-8 sm:left-4 opacity-30 transition-transform duration-500 ease-out hidden md:block"
        style={{
          transform: isTouch
            ? 'rotate(-14deg)'
            : `translate3d(${offset.x * 0.8}px, ${offset.y * 0.8}px, 0) rotate(-14deg)`,
        }}
      >
        <div className="w-32 h-44 bg-[#E2D8C3] rounded-[1px] p-2.5 shadow-xl relative border border-black/10 overflow-hidden">
          {/* Faded faux resume lines */}
          <div className="w-16 h-2 bg-[#2B2620]/30 rounded-[1px] mb-2" />
          <div className="w-24 h-1 bg-[#2B2620]/20 rounded-[1px] mb-3" />
          <div className="space-y-1.5 opacity-40">
            <div className="w-full h-1 bg-[#2B2620]/20" />
            <div className="w-5/6 h-1 bg-[#2B2620]/20" />
            <div className="w-4/6 h-1 bg-[#2B2620]/20" />
          </div>

          {/* Giant Stamped Red Pen X */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-display text-4xl text-[#E8422D]/70 font-bold transform -rotate-12 border-2 border-[#E8422D]/70 px-1 py-0 leading-none">
              REJECT
            </span>
          </div>
        </div>
      </div>

      {/* ── 3. Handwritten Sticky Note (Top-Right) ── */}
      <div
        className="absolute top-24 right-2 sm:right-12 transition-transform duration-300 ease-out z-10"
        style={{
          transform: isTouch
            ? `rotate(${stickyRotation}deg)`
            : `translate3d(${offset.x * -0.7}px, ${offset.y * -0.7}px, 0) rotate(${stickyRotation}deg)`,
        }}
      >
        <div className="w-36 sm:w-44 bg-[#FFF59D] text-[#2B2620] p-3 shadow-md rounded-[1px] border border-amber-300/40 relative">
          {/* Subtle pin/tape shadow at top */}
          <div className="w-8 h-2 bg-amber-400/30 mx-auto -mt-3 mb-1 rounded-[1px]" />
          <p className="font-handwritten text-lg sm:text-xl leading-tight font-bold text-[#8A2B1E]">
            "{stickyText}"
          </p>
        </div>
      </div>
    </div>
  )
}
