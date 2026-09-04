import { useState } from 'react'
import type { Issue } from '@/store/useAppStore'
import { getHinglishTag } from '@/utils/categoryTags'

interface WorstLineTrophyProps {
  issue: Issue
  candidateName?: string
}

export default function WorstLineTrophy({ issue, candidateName }: WorstLineTrophyProps) {
  const [copied, setCopied] = useState(false)

  const tagLabel = issue.badge_label?.trim() || getHinglishTag(issue.category)

  const shareText = `🏆 BUZZWORD CHAMPION TROPHY 🏆\n\nMere resume ki sabse bekaar line pakdi gayi 😂:\n"${issue.quoted_text}"\n\nRed Pen Verdict: "${issue.roast}"\n\nApna resume test karwao: https://resumeroast.app`
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`

  const handleCopyStatus = async () => {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(shareText)
      setCopied(true)
      setTimeout(() => setCopied(false), 3000)
    }
  }

  return (
    <div className="w-full max-w-[640px] mx-auto bg-gradient-to-br from-[#24130F] to-[#17140F] border-2 border-dashed border-stamp/60 rounded-sm p-6 text-left relative overflow-hidden shadow-2xl">
      {/* Top Banner Tag */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="inline-flex items-center gap-2 bg-stamp/20 border border-stamp text-stamp px-3 py-1 rounded-sm">
          <span className="text-base">🏆</span>
          <span className="font-mono text-xs font-bold uppercase tracking-wider">
            WORST BULLET TROPHY // BUZZWORD CHAMPION
          </span>
        </div>

        <span className="font-mono text-[10px] text-amber-300/80 uppercase tracking-widest px-2 py-0.5 border border-amber-300/30 rounded-sm">
          {tagLabel}
        </span>
      </div>

      {/* Quoted Crime */}
      <div className="bg-black/60 border border-white/10 rounded-sm p-4 mb-4">
        <p className="font-mono text-xs text-tan-dim uppercase mb-1 tracking-wider">
          Desk pe pakdi gayi sabse cringe line:
        </p>
        <p className="font-mono text-sm text-paper font-semibold leading-relaxed">
          "{issue.quoted_text}"
        </p>
      </div>

      {/* Savage Callout */}
      <p className="font-body text-sm text-tan leading-relaxed mb-5">
        <span className="text-stamp font-bold mr-1">Verdict:</span>
        {issue.roast}
      </p>

      {/* Share Actions - WhatsApp First */}
      <div className="pt-3 border-t border-white/[0.08] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <span className="font-mono text-xs text-tan-dim">
          Dosto ko bhej ke unka din banao 😂
        </span>

        <div className="flex items-center gap-2">
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary !py-1.5 !px-4 !text-xs !bg-emerald-600 hover:!bg-emerald-500 !border-emerald-500 flex items-center justify-center gap-1.5 font-bold"
          >
            <span>Status pe daal de</span>
            <span>📲</span>
          </a>

          <button
            type="button"
            onClick={handleCopyStatus}
            className="btn-ghost !py-1.5 !px-3 !text-xs"
          >
            {copied ? '✓ Copied!' : 'Copy Text'}
          </button>
        </div>
      </div>
    </div>
  )
}
