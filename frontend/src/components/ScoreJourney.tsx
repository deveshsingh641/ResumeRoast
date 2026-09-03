import React from 'react'
import { Link } from 'react-router-dom'
import type { ScoreBand } from '@/store/useAppStore'

interface ScoreJourneyProps {
  currentScore: number
  band: ScoreBand
  totalIssues?: number
}

export default function ScoreJourney({ currentScore, band, totalIssues = 6 }: ScoreJourneyProps) {
  // Calculate milestone scores dynamically
  const step1Gain = 25
  const step2Gain = 18
  const step3Gain = 14

  const scoreStep1 = Math.min(65, currentScore + step1Gain)
  const scoreStep2 = Math.min(82, scoreStep1 + step2Gain)
  const scoreStep3 = Math.min(96, Math.max(85, scoreStep2 + step3Gain))

  return (
    <div className="w-full max-w-[640px] mx-auto bg-gradient-to-b from-[#181410] to-[#120F0C] border border-white/[0.08] rounded-sm p-6 text-left relative overflow-hidden shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-4 border-b border-white/[0.08] pb-3">
        <div>
          <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold block">
            ROADMAP // FIX KARNE KA PLAN
          </span>
          <h3 className="font-display text-lg sm:text-xl text-paper">
            Score Journey: {currentScore} se 85+ tak ka safar 🚀
          </h3>
        </div>
        <div className="text-right">
          <span className="font-mono text-xs text-tan-dim block">Current Baseline</span>
          <span className="font-display text-xl text-stamp font-bold">{currentScore}/100</span>
        </div>
      </div>

      <p className="font-mono text-xs text-tan-dim mb-6 leading-relaxed">
        Ye {totalIssues} galtiyan theek karne se tera resume sidha Top 5% ATS filter mein enter kar sakta hai.
      </p>

      {/* Steps Visual Track */}
      <div className="space-y-4">
        {/* Step 1 */}
        <div className="flex items-start gap-3.5 bg-black/30 border border-white/[0.06] rounded-sm p-3.5 transition-all hover:border-amber-400/30">
          <div className="w-8 h-8 rounded-full bg-stamp/20 border border-stamp text-stamp font-mono text-xs font-bold flex items-center justify-center shrink-0">
            01
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-body text-sm font-semibold text-paper">
                Numbers aur Metrics daalo
              </h4>
              <span className="font-mono text-xs text-emerald-400 font-bold bg-emerald-950/40 px-2 py-0.5 rounded-sm">
                +{step1Gain} pts → ~{scoreStep1}
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              Har bullet point mein %, $, ya counts daalo. Recruiter ko pata chalna chahiye kitna scale kiya.
            </p>
          </div>
        </div>

        {/* Step 2 */}
        <div className="flex items-start gap-3.5 bg-black/30 border border-white/[0.06] rounded-sm p-3.5 transition-all hover:border-amber-400/30">
          <div className="w-8 h-8 rounded-full bg-ember/20 border border-ember text-ember font-mono text-xs font-bold flex items-center justify-center shrink-0">
            02
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-body text-sm font-semibold text-paper">
                Buzzwords & Jargon hatao
              </h4>
              <span className="font-mono text-xs text-emerald-400 font-bold bg-emerald-950/40 px-2 py-0.5 rounded-sm">
                +{step2Gain} pts → ~{scoreStep2}
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              "Synergistic", "responsible for", "passionate" jaise words cut karke direct action verbs use karo.
            </p>
          </div>
        </div>

        {/* Step 3 */}
        <div className="flex items-start gap-3.5 bg-black/30 border border-white/[0.06] rounded-sm p-3.5 transition-all hover:border-amber-400/30">
          <div className="w-8 h-8 rounded-full bg-emerald-500/20 border border-emerald-500 text-emerald-400 font-mono text-xs font-bold flex items-center justify-center shrink-0">
            03
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h4 className="font-body text-sm font-semibold text-paper">
                Formatting & Spacing Clean Karo
              </h4>
              <span className="font-mono text-xs text-emerald-400 font-bold bg-emerald-950/40 px-2 py-0.5 rounded-sm">
                +{step3Gain} pts → ~{scoreStep3}
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              1-page layout, standard margins, aur zero typos. ATS parser 100% clean extract karega.
            </p>
          </div>
        </div>
      </div>

      {/* Target Milestone Banner */}
      <div className="mt-5 p-3 bg-gradient-to-r from-emerald-950/30 to-black/40 border border-emerald-500/30 rounded-sm flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🏆</span>
          <div>
            <span className="font-mono text-[11px] text-emerald-300 font-bold block">
              FINAL GOAL: 85+ (Shortlist Ready)
            </span>
            <span className="font-mono text-[10px] text-tan-dim">
              Recruiter ke samne aate hi interview call aayega
            </span>
          </div>
        </div>
        <Link to="/roast" className="btn-ghost !py-1 !px-3 !text-xs text-emerald-400 hover:text-emerald-300">
          Fix karke dobara roast karo →
        </Link>
      </div>
    </div>
  )
}
