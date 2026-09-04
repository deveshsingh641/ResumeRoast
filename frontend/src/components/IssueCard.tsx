import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import type { Issue } from '@/store/useAppStore'
import { getHinglishTag } from '@/utils/categoryTags'

export function getCategoryColor(category: string): string {
  switch (category) {
    case 'buzzword':
    case 'no-metrics':
    case 'typo':
      return '#E8422D' // --stamp
    case 'formatting':
    case 'length':
      return '#FFB93C' // --ember
    default:
      return '#8A8168' // --tan-dim
  }
}

interface IssueCardProps {
  issue: Issue
  rank: number
  locked?: boolean
  roastId?: string
}

export function IssueCard({ issue, rank, locked = false, roastId = 'default' }: IssueCardProps) {
  const [showFix, setShowFix] = useState(false)
  const categoryColor = getCategoryColor(issue.category)
  const tagLabel = issue.badge_label?.trim() || getHinglishTag(issue.category)

  // 1.2 WhatsApp "Typing..." Indicator State & Session Cache
  const cardRef = useRef<HTMLDivElement>(null)
  const cacheKey = `seen_roast_${roastId}_issue_${rank}_${issue.quoted_text.slice(0, 20)}`
  const alreadySeen = typeof window !== 'undefined' && Boolean(sessionStorage.getItem(cacheKey))

  const [isTyping, setIsTyping] = useState(false)
  const [isRevealed, setIsRevealed] = useState(alreadySeen || locked)

  useEffect(() => {
    if (alreadySeen || locked || isRevealed) return

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries
        if (entry.isIntersecting) {
          setIsTyping(true)
          const timer = setTimeout(() => {
            setIsTyping(false)
            setIsRevealed(true)
            try {
              sessionStorage.setItem(cacheKey, 'true')
            } catch {}
          }, 650)
          observer.disconnect()
          return () => clearTimeout(timer)
        }
      },
      { threshold: 0.15 }
    )

    if (cardRef.current) {
      observer.observe(cardRef.current)
    }

    return () => observer.disconnect()
  }, [alreadySeen, locked, isRevealed, cacheKey])

  return (
    <div
      ref={cardRef}
      className="relative bg-bg border border-white/[0.08] rounded-r-sm rounded-l-none p-5 select-none transition-all duration-200 hover:-translate-y-[3px] hover:shadow-2xl hover:border-white/[0.16] group"
      style={{
        borderLeft: `3px solid ${categoryColor}`,
      }}
    >
      {/* Locked overlay (Frosted blur over real content) */}
      {locked && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 backdrop-blur-[6px] bg-bg/70 px-4 text-center rounded-r-sm">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#8A8168"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <p className="font-mono text-xs text-tan">
            Issue #{rank} Free tier mein locked hai bhai 🔒
          </p>
          <Link
            to={typeof window !== 'undefined' ? `/pricing?from=${encodeURIComponent(window.location.pathname)}` : '/pricing'}
            className="btn-ghost btn-ghost-sm"
          >
            Poora roast unlock karo
          </Link>
        </div>
      )}

      {/* Main card content */}
      <div className={locked ? 'select-none pointer-events-none' : ''}>
        {/* Header Row */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span
            className="font-mono text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-sm transition-all duration-200 group-hover:brightness-125"
            style={{
              color: categoryColor,
              backgroundColor: `${categoryColor}15`,
              border: `1px solid ${categoryColor}40`,
            }}
          >
            {tagLabel}
          </span>
          <span className="font-mono text-xs text-tan-dim">
            #{String(rank).padStart(2, '0')}
          </span>
        </div>

        {/* Monospace Quoted Original Text with subtle --paper wash */}
        <div className="font-mono text-xs text-paper bg-[#F5EFE0]/[0.06] border border-white/[0.04] rounded-sm px-3 py-2 mb-3 leading-relaxed">
          <span className="text-tan-dim select-none mr-1">"</span>
          <span className="text-paper">{issue.quoted_text}</span>
          <span className="text-tan-dim select-none ml-1">"</span>
        </div>

        {/* 1.2 WhatsApp Typing Indicator Understated Bouncing Dots Bubble */}
        {isTyping && !isRevealed && (
          <div
            role="status"
            aria-label="Roast line typing..."
            className="flex items-center gap-2 py-1 px-3 bg-white/[0.04] border border-white/[0.08] rounded-full w-fit mb-3 select-none"
          >
            <span className="font-mono text-[10px] text-tan-dim tracking-wider">typing…</span>
            <div className="flex items-center gap-1.5 py-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-tan-dim typing-dot" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-tan-dim typing-dot" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-tan-dim typing-dot" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        )}

        {/* Brutally honest critique text (Revealed once typing completes) */}
        {isRevealed && (
          <p className="font-body text-sm text-tan mb-3 leading-relaxed animate-fadeIn">
            {issue.roast}
          </p>
        )}

        {/* Fix button & toggleable suggested rewrite */}
        {isRevealed && issue.fix && (
          <div>
            <button
              type="button"
              onClick={() => setShowFix((v) => !v)}
              className="font-mono text-xs text-ember hover:underline flex items-center gap-1.5 focus:outline-none"
              aria-expanded={showFix}
            >
              <span className="select-none">{showFix ? '−' : '+'}</span>
              <span>{showFix ? 'Fix chhupao (−)' : 'Fix dekh le (+)'}</span>
            </button>

            {showFix && (
              <div className="mt-2 bg-[#F5EFE0]/[0.04] border border-white/[0.08] rounded-sm p-3">
                <p className="font-mono text-xs text-tan-dim mb-1 uppercase tracking-wider">
                  Aise Likhna Chahiye Tha:
                </p>
                <p className="font-mono text-xs text-paper leading-relaxed">
                  {issue.fix}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

interface IssueListProps {
  issues: Issue[]
  totalIssues: number
  isTruncated: boolean
  roastId?: string
}

export function IssueList({ issues, totalIssues, isTruncated, roastId }: IssueListProps) {
  const lockedCount = isTruncated ? Math.max(0, totalIssues - issues.length) : 0

  // Real placeholder locked cards for layout-shift-free preview
  const lockedCards: Issue[] = [
    {
      quoted_text: 'Assisted team members with various ad-hoc engineering duties as needed.',
      category: 'no-metrics',
      roast: '"Assisted" likh ke credit kyu gawa rahe ho yaar? Exact metric batao na.',
      fix: 'Rewrite karo: "Resolved 45+ critical production bugs in PostgreSQL, reducing ticket backlog by 40%".',
      start_offset: null,
      end_offset: null,
      severity_rank: 4,
    },
    {
      quoted_text: 'Passionate self-starter with deep enthusiasm for next-generation technology.',
      category: 'buzzword',
      roast: 'Pure buzzword filler hai bhai, recruiter eye-tracking mein instantly skip hota hai 🥱',
      fix: 'Adjectives hatao aur shipped projects ke live stack aur metrics daalo.',
      start_offset: null,
      end_offset: null,
      severity_rank: 5,
    },
    {
      quoted_text: 'Curriculum Vitae — References available upon request.',
      category: 'formatting',
      roast: 'Prime resume space waste ho raha hai bhai, standard baatein likh ke 💀',
      fix: 'Ye line delete karke vertical whitespace ko project links ke liye use karo.',
      start_offset: null,
      end_offset: null,
      severity_rank: 6,
    },
  ].slice(0, lockedCount)

  return (
    <div className="space-y-3 w-full max-w-[640px] mx-auto text-left">
      {issues.map((issue, idx) => (
        <IssueCard key={idx} issue={issue} rank={idx + 1} locked={false} roastId={roastId} />
      ))}
      {lockedCards.map((issue, idx) => (
        <IssueCard key={`locked-${idx}`} issue={issue} rank={issues.length + idx + 1} locked={true} roastId={roastId} />
      ))}
    </div>
  )
}
