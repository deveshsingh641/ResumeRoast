import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'

const HINGLISH_ROAST_LINES = [
  '⚡ "Bhai resume hai ya suspense novel? Recruiter ko number chahiye, kahani nahi." 🕵️',
  '⚡ "Responsible for likhna band karo yaar 😩 impact dikhao!"',
  '⚡ "4 page ka resume? Novel likh rahe ho kya bhai?" 💀',
  '⚡ "Worked closely with design team — matlab chai piya ya code likha? ☕"',
  '⚡ "Hobbies section hatao boss, biodata thodi hai 😅"',
  '⚡ "Declaration 2005 ka kyu daal rakha hai? ✋"',
  '⚡ "Arre yaar spellcheck skip kar diya kya? 🤡"',
]

const ENGLISH_ROAST_LINES = [
  '⚡ "Is this a resume or a mystery novel? Recruiters need metrics, not cliffhangers." 🕵️',
  '⚡ "Stop writing \'Responsible for\' 😩 Show what actually shipped!"',
  '⚡ "Four pages? Recruiters give this six seconds, not a book review." 💀',
  '⚡ "\'Worked closely with design team\' — so who wrote the code? ☕"',
  '⚡ "Cut the hobbies section. This is a resume, not a dating profile 😅"',
  '⚡ "Declarations and signatures retired in 2005 ✋ Reclaim the whitespace."',
  '⚡ "Spellcheck is free and faster than an automated rejection 🤡"',
]

export default function MarqueeTicker() {
  const { i18n } = useTranslation()
  const [isPaused, setIsPaused] = useState(false)
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const lines = isHinglish ? HINGLISH_ROAST_LINES : ENGLISH_ROAST_LINES

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
        {lines.concat(lines).map((line, idx) => (
          <span key={idx} className="flex items-center gap-2 hover:text-tan transition-colors">
            {line}
          </span>
        ))}
      </div>
    </div>
  )
}
