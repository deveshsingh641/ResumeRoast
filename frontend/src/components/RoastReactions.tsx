import { useState, useEffect } from 'react'
import axios from 'axios'

interface RoastReactionsProps {
  roastId: string
  className?: string
}

type EmojiType = 'laugh' | 'fire' | 'skull' | 'eyes'

interface ReactionConfig {
  key: EmojiType
  symbol: string
  label: string
}

const REACTION_CONFIGS: ReactionConfig[] = [
  { key: 'laugh', symbol: '😂', label: 'Hansi aa gayi' },
  { key: 'fire',  symbol: '🔥', label: 'Bohot savage roast' },
  { key: 'skull', symbol: '💀', label: 'Dead bhai' },
  { key: 'eyes',  symbol: '👀', label: 'Dekh raha hu' },
]

export default function RoastReactions({ roastId, className = '' }: RoastReactionsProps) {
  const [reactions, setReactions] = useState<Record<string, number>>({
    laugh: 0,
    fire: 0,
    skull: 0,
    eyes: 0,
  })
  const [userReacted, setUserReacted] = useState<Record<string, number>>({})
  const [bouncingEmoji, setBouncingEmoji] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Local storage key for session tracking per roast
  const sessionKey = `reactions_roast_${roastId}`

  useEffect(() => {
    // Load existing user reactions from local storage
    try {
      const saved = localStorage.getItem(sessionKey)
      if (saved) {
        setUserReacted(JSON.parse(saved))
      }
    } catch {}

    // Fetch live reaction counts from API
    const fetchReactions = async () => {
      try {
        const { data } = await axios.get(`/api/roast/${roastId}/reactions`, { timeout: 8000 })
        if (data?.reactions) {
          setReactions(data.reactions)
        }
      } catch {
        // Silently retain defaults if demo or offline
      }
    }

    if (roastId) {
      fetchReactions()
    }
  }, [roastId, sessionKey])

  const handleReact = async (key: EmojiType) => {
    // Rate limit: max 6 total reactions per person on this roast
    const totalUserReacts = Object.values(userReacted).reduce((a, b) => a + b, 0)
    if (totalUserReacts >= 6) {
      return
    }

    // Optimistic UI update
    setReactions((prev) => ({
      ...prev,
      [key]: (prev[key] || 0) + 1,
    }))

    const nextUserReacted = {
      ...userReacted,
      [key]: (userReacted[key] || 0) + 1,
    }
    setUserReacted(nextUserReacted)
    try {
      localStorage.setItem(sessionKey, JSON.stringify(nextUserReacted))
    } catch {}

    // Micro-animation trigger
    setBouncingEmoji(key)
    setTimeout(() => setBouncingEmoji(null), 400)

    try {
      setIsSubmitting(true)
      const { data } = await axios.post(`/api/roast/${roastId}/react`, { emoji: key }, { timeout: 8000 })
      if (data?.reactions) {
        setReactions(data.reactions)
      }
    } catch {
      // In offline or demo mode, optimistic state remains
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      role="region"
      aria-label="Roast Emoji Reactions"
      className={`inline-flex flex-col sm:flex-row items-center gap-3 p-2.5 rounded-sm border border-white/[0.08] bg-white/[0.02] backdrop-blur-xs select-none ${className}`}
    >
      <div className="flex items-center gap-1.5 text-left">
        <span className="text-xs">💬</span>
        <span className="font-mono text-[11px] text-tan-dim tracking-wider uppercase">
          React Karo:
        </span>
      </div>

      <div className="flex items-center gap-2">
        {REACTION_CONFIGS.map((item) => {
          const count = reactions[item.key] || 0
          const hasUserReacted = (userReacted[item.key] || 0) > 0
          const isBouncing = bouncingEmoji === item.key

          return (
            <button
              key={item.key}
              type="button"
              onClick={() => handleReact(item.key)}
              title={item.label}
              aria-label={`${item.label} (${count} reactions)`}
              className={`group relative flex items-center gap-1.5 px-3 py-1.5 rounded-sm border transition-all duration-150 focus:outline-none ${
                hasUserReacted
                  ? 'border-amber-500/40 bg-amber-500/10 text-paper shadow-sm'
                  : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] hover:border-white/[0.14] text-tan-dim hover:text-tan'
              } ${isBouncing ? 'scale-110 -translate-y-0.5' : 'hover:-translate-y-0.5'}`}
            >
              <span className={`text-base leading-none transition-transform duration-150 ${isBouncing ? 'scale-125' : 'group-hover:scale-115'}`}>
                {item.symbol}
              </span>

              {/* Show count badge ONLY if count > 0 (Never display a row of empty zeros) */}
              {count > 0 && (
                <span className="font-mono text-xs font-semibold text-paper/90 ml-0.5 animate-fadeIn">
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
