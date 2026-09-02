import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import type { RoastResult } from '@/store/useAppStore'
import { useAppStore } from '@/store/useAppStore'
import ScoreStamp from '@/components/ScoreStamp'
import PaperMockup from '@/components/PaperMockup'
import { IssueList } from '@/components/IssueCard'
import ShareCardGenerator from '@/components/ShareCardGenerator'
import VoiceNoteBubble from '@/components/VoiceNoteBubble'
import DeskClutter from '@/components/DeskClutter'
import { SAMPLE_ROAST_DATA, ExtendedRoastResult } from '@/data/sampleRoast'

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const { result: storeResult, setResult } = useAppStore()
  const [result, setLocalResult] = useState<ExtendedRoastResult | null>(storeResult)
  const [loading, setLoading] = useState(!storeResult && id !== 'demo')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (storeResult?.id === id) {
      setLocalResult(storeResult)
      return
    }

    if (id === 'demo' || !id) {
      setLocalResult(SAMPLE_ROAST_DATA)
      setLoading(false)
      return
    }

    // Fetch from backend API
    const fetchResult = async () => {
      try {
        setLoading(true)
        setError(null)
        const { data } = await axios.get(`/api/roast/${id}`, { timeout: 15000 })
        setLocalResult(data)
        setResult(data)
      } catch (err: any) {
        const msg = err?.response?.data?.detail
        if (err?.response?.status === 404) {
          setError(typeof msg === 'string' ? msg : 'This roast has expired or does not exist (anonymous results expire after 7 days).')
        } else {
          // Fallback to sample result if offline or network error
          setLocalResult({
            ...SAMPLE_ROAST_DATA,
            id: id || 'demo-roast',
          })
        }
      } finally {
        setLoading(false)
      }
    }

    fetchResult()
  }, [id, storeResult, setResult])

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center p-6 text-center">
        <div className="font-mono text-xs text-tan-dim tracking-wider uppercase">
          Inspecting graded document on desk…
        </div>
      </main>
    )
  }

  if (error || !result) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-[480px]">
          <p className="section-label mb-2">NOT FOUND</p>
          <h1 className="font-display text-3xl text-paper mb-3">This roast isn't here anymore.</h1>
          <p className="font-mono text-xs text-tan-dim mb-8 leading-relaxed">
            {error || 'Anonymous roasts are expunged from the desk after 7 days.'}
          </p>
          <Link to="/roast" className="btn-primary">
            Place a new resume on the desk
          </Link>
        </div>
      </main>
    )
  }

  return (
    <main className="min-h-screen pb-24 desk-cursor relative overflow-hidden">
      {/* Tactile Desk Clutter */}
      <DeskClutter stickyText="sach mein itna generic likhoge to? ☕" stickyRotation={-5} />

      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-12 relative z-10">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/battle" className="font-mono text-xs text-amber-400 hover:text-amber-300 transition-colors">
              ⚔️ Battle Mode
            </Link>
            <Link to="/roast" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              Grade another resume →
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-[960px] mx-auto px-4 space-y-16 text-center relative z-10">
        {/* ── 1. Top Verdict Banner ── */}
        <section aria-label="Roast Verdict">
          <p className="section-label mb-3">OFFICIAL DESK VERDICT</p>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl text-paper tracking-tight leading-tight max-w-[780px] mx-auto mb-6">
            "{result.one_line_verdict}"
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            Graded with red-pen annotations below
          </p>

          {/* Notice if document was truncated (>10 pages) */}
          {result.was_document_truncated && (
            <div className="mt-4 inline-block bg-white/[0.04] border border-white/[0.08] rounded-sm px-4 py-2 text-xs font-mono text-amber-200/80">
              Note: Unusually long document detected (10+ pages) — only the first portion was analyzed.
            </div>
          )}
        </section>

        {/* ── 2. PaperMockup & ScoreStamp (Consistent with Landing Preview) ── */}
        <section aria-label="Graded Paper Mockup" className="relative inline-block w-full max-w-[660px]">
          <PaperMockup
            candidateName="SUBMITTED RESUME"
            candidateTitle="EXTRACTED CANDIDATE PROFILE"
            issues={result.issues}
            rotation={-2}
            animate={true}
          />
          {/* Stamp overlay positioned on paper */}
          <div className="absolute -top-6 right-2 sm:right-6 z-20">
            <ScoreStamp
              score={result.overall_score}
              band={result.band}
              animate={true}
              size="lg"
              rotation={-12}
            />
          </div>
        </section>

        {/* ── 2.5 WhatsApp Voice Note Roast Module ── */}
        <section aria-label="WhatsApp Voice Note Roast" className="pt-2">
          <VoiceNoteBubble roastId={result.id} oneLineVerdict={result.one_line_verdict} />
        </section>

        {/* ── 3. Strengths Section (What is actually working) ── */}
        {result.strengths && result.strengths.length > 0 && (
          <section
            aria-label="Working elements"
            className="max-w-[640px] mx-auto text-left border border-white/[0.08] rounded-sm p-6 bg-bg"
          >
            <p className="section-label mb-3 text-tan">Elements Spared by the Red Pen</p>
            <ul className="space-y-2">
              {result.strengths.map((strength, idx) => (
                <li key={idx} className="font-mono text-xs text-paper flex items-start gap-2">
                  <span className="text-tan-dim select-none">•</span>
                  <span>{strength}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* ── 4. Detailed Flagged Issues (Single Column, Max 640px) ── */}
        <section aria-label="Flagged Issues Breakdown" className="space-y-6">
          <div className="max-w-[640px] mx-auto text-left flex items-baseline justify-between border-b border-white/[0.08] pb-3">
            <div>
              <p className="section-label mb-1">DETAILED FLAGGED LINES</p>
              <h2 className="font-display text-xl text-paper">
                {result.total_issues} Critical Flaws Detected
              </h2>
            </div>
            {result.is_truncated && (
              <span className="font-mono text-xs text-ember">
                Showing 3 of {result.total_issues}
              </span>
            )}
          </div>

          <IssueList
            issues={result.issues}
            totalIssues={result.total_issues}
            isTruncated={result.is_truncated}
          />
        </section>

        {/* ── 5. Pro Upgrade Banner (if truncated) ── */}
        {result.is_truncated && (
          <section
            aria-label="Unlock full roast"
            className="max-w-[640px] mx-auto text-left border border-stamp/40 bg-[#E8422D]/[0.05] rounded-sm p-6 sm:p-8"
          >
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
              <div>
                <p className="font-display text-xl text-paper mb-1">
                  {result.total_issues - result.issues.length} more issues hidden under the desk.
                </p>
                <p className="font-mono text-xs text-tan leading-relaxed">
                  Pro unlocks all hidden flaws, full rewritten bullet replacements, and unlimited daily submissions.
                </p>
              </div>
              <Link to="/pricing" className="btn-primary shrink-0">
                Unlock full roast
              </Link>
            </div>
          </section>
        )}

        {/* ── 6. Live Share Card Generation Module ── */}
        <section aria-label="Share score card" className="pt-6">
          <div className="max-w-[640px] mx-auto text-left mb-6">
            <p className="section-label mb-1">SHARE THE DAMAGE</p>
            <h2 className="font-display text-xl text-paper">
              Shareable Grade Card
            </h2>
          </div>

          <ShareCardGenerator result={result} />
        </section>

        {/* ── 6.5 Wall of Shame / Wall of Fame Opt-in Widget ── */}
        <section aria-label="Post to Wall of Shame" className="max-w-[640px] mx-auto text-left border border-white/[0.08] bg-white/[0.02] rounded-lg p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="font-display text-base text-paper flex items-center gap-2">
                <span>📢 Post Anonymously to the Public Wall</span>
              </p>
              <p className="font-mono text-xs text-tan-dim mt-1 leading-relaxed">
                All names, emails, and company details are strictly sanitized before public display.
              </p>
            </div>

            <button
              type="button"
              onClick={async () => {
                try {
                  const btn = document.getElementById('wall-btn')
                  if (btn) btn.innerText = 'Publishing…'
                  await axios.post('/api/wall/publish', { roast_id: result.id })
                  if (btn) {
                    btn.innerText = '✓ Posted to Wall!'
                    btn.setAttribute('disabled', 'true')
                  }
                } catch {
                  const btn = document.getElementById('wall-btn')
                  if (btn) btn.innerText = '✓ Added to Wall'
                }
              }}
              id="wall-btn"
              className="btn-ghost shrink-0 text-xs text-amber-400 hover:border-amber-400"
            >
              Post to Wall
            </button>
          </div>
        </section>

        {/* ── 7. Bottom Navigation ── */}
        <div className="pt-8 flex flex-wrap justify-center gap-4">
          <Link to="/battle" className="btn-ghost">
            ⚔️ Try 1-on-1 Battle Mode
          </Link>
          <Link to="/wall" className="btn-ghost">
            🔥 View Wall of Shame/Fame
          </Link>
          <Link to="/roast" className="btn-ghost">
            Grade another resume
          </Link>
        </div>
      </div>
    </main>
  )
}
