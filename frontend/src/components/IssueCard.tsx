import { useState } from 'react'
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
}

export function IssueCard({ issue, rank, locked = false }: IssueCardProps) {
  const [showFix, setShowFix] = useState(false)
  const categoryColor = getCategoryColor(issue.category)
  const tagLabel = getHinglishTag(issue.category)

  return (
    <div
      className="relative bg-bg border border-white/[0.08] rounded-r-sm rounded-l-none p-5 select-none transition-colors duration-120"
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
          <a href="/pricing" className="btn-ghost btn-ghost-sm">
            Poora roast unlock karo
          </a>
        </div>
      )}

      {/* Main card content */}
      <div className={locked ? 'select-none pointer-events-none' : ''}>
        {/* Header Row */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span
            className="font-mono text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-sm"
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

        {/* Brutally honest critique text */}
        <p className="font-body text-sm text-tan mb-3 leading-relaxed">
          {issue.roast}
        </p>

        {/* Fix button & toggleable suggested rewrite */}
        {issue.fix && (
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
}

export function IssueList({ issues, totalIssues, isTruncated }: IssueListProps) {
  const lockedCount = isTruncated ? Math.max(0, totalIssues - issues.length) : 0

  // Real placeholder locked cards for layout-shift-free preview
  const lockedCards: Issue[] = [
    {
      quoted_text: 'Assisted team members with various ad-hoc engineering duties as needed.',
      category: 'no-metrics',
      roast: 'Vague filler sentence that adds zero quantifiable substance to your experience.',
      fix: 'Specify 2-3 specific technical implementations and their measurable impact.',
      start_offset: null,
      end_offset: null,
      severity_rank: 4,
    },
    {
      quoted_text: 'Passionate self-starter with deep enthusiasm for next-generation technology.',
      category: 'buzzword',
      roast: 'Pure buzzword filler that recruiter eye-tracking studies prove gets skipped instantly.',
      fix: 'Cut entirely and replace with actual tools, frameworks, and architecture patterns.',
      start_offset: null,
      end_offset: null,
      severity_rank: 5,
    },
    {
      quoted_text: 'Curriculum Vitae — References available upon request.',
      category: 'formatting',
      roast: 'Wastes a prime line of document real estate stating standard procedure.',
      fix: 'Delete this line immediately to free up vertical spacing.',
      start_offset: null,
      end_offset: null,
      severity_rank: 6,
    },
  ].slice(0, lockedCount)

  return (
    <div className="space-y-3 w-full max-w-[640px] mx-auto text-left">
      {issues.map((issue, idx) => (
        <IssueCard key={idx} issue={issue} rank={idx + 1} locked={false} />
      ))}
      {lockedCards.map((issue, idx) => (
        <IssueCard key={`locked-${idx}`} issue={issue} rank={issues.length + idx + 1} locked={true} />
      ))}
    </div>
  )
}
