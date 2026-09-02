import { useState } from 'react'

const ROAST_LINES = [
  '⚡ "Bhai resume hai ya suspense novel? Recruiter ko number chahiye, kahani nahi." 🕵️',
  '⚡ "Responsible for likhna band karo yaar 😩 impact dikhao!"',
  '⚡ "4 page ka resume? Novel likh rahe ho kya bhai?" 💀',
  '⚡ "Worked closely with design team — matlab chai piya ya code likha? ☕"',
  '⚡ "Hobbies section hatao boss, biodata thodi hai 😅"',
  '⚡ "Declaration 2005 ka kyu daal rakha hai? ✋"',
  '⚡ "Arre yaar spellcheck skip kar diya kya? 🤡"',
]

export default function MarqueeTicker() {
  const [isPaused, setIsPaused] = useState(false)

  return (
    <div
      className="w-full bg-[#1A1612] border-y border-white/[0.08] py-2 overflow-hidden select-none"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      role="region"
      aria-label="Live roast ticker"
    >
      <div
        className="flex whitespace-nowrap gap-12 text-xs font-mono text-tan-dim"
        style={{
          animation: isPaused ? 'none' : 'marquee 35s linear infinite',
          display: 'inline-flex',
        }}
      >
        {ROAST_LINES.concat(ROAST_LINES).map((line, idx) => (
          <span key={idx} className="flex items-center gap-2 hover:text-tan transition-colors">
            {line}
          </span>
        ))}
      </div>
    </div>
  )
}
