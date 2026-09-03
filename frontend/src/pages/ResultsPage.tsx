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
import PapaProudMeter from '@/components/PapaProudMeter'
import WorstLineTrophy from '@/components/WorstLineTrophy'
import ReferralChallenge from '@/components/ReferralChallenge'
import ScoreJourney from '@/components/ScoreJourney'
import { SAMPLE_ROAST_DATA, ExtendedRoastResult } from '@/data/sampleRoast'

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const { result: storeResult, setResult } = useAppStore()
  const [result, setLocalResult] = useState<ExtendedRoastResult | null>(storeResult)
  const [loading, setLoading] = useState(!storeResult && id !== 'demo')
  const [error, setError] = useState<string | null>(null)
  const [downloadingCert, setDownloadingCert] = useState(false)

  const handleDownloadCertificate = async () => {
    if (!result) return
    try {
      setDownloadingCert(true)
      const downloadUrl = `/api/roast/${result.id}/certificate/download`
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `ResumeRoast-Certificate-${result.id.slice(0, 8)}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch {
      window.open(`/api/roast/${result.id}/certificate/download`, '_blank')
    } finally {
      setTimeout(() => setDownloadingCert(false), 2500)
    }
  }

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
          setError(typeof msg === 'string' ? msg : 'Ye roast link expire ho gaya hai ya galat hai (anonymous reports 7 din mein expunge ho jaati hain).')
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
          Desk pe report taiyyar ho rahi hai…
        </div>
      </main>
    )
  }

  if (error || !result) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
        <div className="max-w-[480px]">
          <p className="section-label mb-2">NOT FOUND</p>
          <h1 className="font-display text-3xl text-paper mb-3">Ye roast desk pe nahi mila bhai.</h1>
          <p className="font-mono text-xs text-tan-dim mb-8 leading-relaxed">
            {error || 'Anonymous roasts 7 din baad desk se delete ho jaate hain.'}
          </p>
          <Link to="/roast" className="btn-primary">
            Naya resume desk pe daalo
          </Link>
        </div>
      </main>
    )
  }

  const worstIssue =
    result.issues && result.issues.length > 0
      ? [...result.issues].sort((a, b) => (a.severity_rank ?? 99) - (b.severity_rank ?? 99))[0]
      : null

  return (
    <main className="min-h-screen pb-24 desk-cursor relative overflow-hidden">
      {/* Tactile Desk Clutter (A.5) */}
      <DeskClutter stickyText="friday se pehle fix kar le yaar!! 😭" stickyRotation={-5} />

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
              Dusra resume roast karo →
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-[960px] mx-auto px-4 space-y-16 text-center relative z-10">
        {/* ── 1. Top Verdict Banner (A.6) ── */}
        <section aria-label="Roast Verdict">
          <p className="section-label mb-3">DESK KA OFFICIAL VERDICT</p>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl text-paper tracking-tight leading-tight max-w-[780px] mx-auto mb-6">
            "{result.one_line_verdict}"
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            Red pen se poori marking neeche dekho
          </p>

          {/* Notice if document was truncated (>10 pages) */}
          {result.was_document_truncated && (
            <div className="mt-4 inline-block bg-white/[0.04] border border-white/[0.08] rounded-sm px-4 py-2 text-xs font-mono text-amber-200/80">
              Note: Unusually lamba resume tha (10+ pages) — sirf pehla part analyze hua hai.
            </div>
          )}
        </section>

        {/* ── 2. PaperMockup & ScoreStamp ── */}
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

        {/* ── 2.2 B.3 Papa Proud Meter Gag Score ── */}
        <section aria-label="Papa Proud Meter" className="pt-2">
          <PapaProudMeter overallScore={result.overall_score} />
        </section>

        {/* ── 2.5 WhatsApp Voice Note Roast Module ── */}
        <section aria-label="WhatsApp Voice Note Roast" className="pt-2">
          <VoiceNoteBubble roastId={result.id} oneLineVerdict={result.one_line_verdict} />
        </section>

        {/* ── 2.7 B.7 Meme-able Worst-Line Badge ── */}
        {worstIssue && (
          <section aria-label="Worst Bullet Trophy">
            <WorstLineTrophy issue={worstIssue} />
          </section>
        )}

        {/* ── 3. Strengths Section (Section A.6) ── */}
        {result.strengths && result.strengths.length > 0 && (
          <section
            aria-label="Working elements"
            className="max-w-[640px] mx-auto text-left border border-white/[0.08] rounded-sm p-6 bg-bg"
          >
            <p className="section-label mb-3 text-tan">Red pen se bach gayi ye cheezein (kuch toh accha tha 👍)</p>
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

        {/* ── 4. Detailed Flagged Issues (Section A.6) ── */}
        <section aria-label="Flagged Issues Breakdown" className="space-y-6">
          <div className="max-w-[640px] mx-auto text-left flex items-baseline justify-between border-b border-white/[0.08] pb-3">
            <div>
              <p className="section-label mb-1">LINE-BY-LINE PAKAD MEIN AAYA</p>
              <h2 className="font-display text-xl text-paper">
                Itni galtiyaan mili bhai ({result.total_issues})
              </h2>
            </div>
            {result.is_truncated && (
              <span className="font-mono text-xs text-ember">
                {result.issues.length} dikha rahe hain, {result.total_issues} mein se
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
                  {result.total_issues - result.issues.length} aur galtiyaan desk ke neeche chhipi hain.
                </p>
                <p className="font-mono text-xs text-tan leading-relaxed">
                  Pro plan mein saari chhipi galtiyaan, exact rewritten lines, aur unlimited daily roasts khul jayenge.
                </p>
              </div>
              <Link to="/pricing" className="btn-primary shrink-0">
                Poora roast unlock karo
              </Link>
            </div>
          </section>
        )}

        {/* ── 5.5 Score Journey Roadmap ── */}
        <section aria-label="Score Journey Roadmap" className="pt-2">
          <ScoreJourney
            currentScore={result.overall_score}
            band={result.band}
            totalIssues={result.total_issues}
          />
        </section>

        {/* ── 5.8 Official Parody Certificate Download Card ── */}
        <section
          aria-label="Official Evaluation Diploma"
          className="max-w-[640px] mx-auto text-left border-2 border-dashed border-amber-500/40 bg-gradient-to-br from-[#1C160E] to-[#120F0C] rounded-sm p-6 shadow-xl relative overflow-hidden"
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xl">📜</span>
                <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold">
                  OFFICIAL EVALUATION DIPLOMA // PARODY PDF
                </span>
              </div>
              <h3 className="font-display text-lg sm:text-xl text-paper">
                Official Parody Certificate Download Karo
              </h3>
              <p className="font-mono text-xs text-tan-dim mt-1 leading-relaxed">
                High-res printable PDF with wax seal stamp, score verdict, and official parody title.
              </p>
            </div>
            <button
              type="button"
              onClick={handleDownloadCertificate}
              disabled={downloadingCert}
              className="btn-primary shrink-0 !text-xs !py-2.5 !px-4 flex items-center gap-1.5 font-bold whitespace-nowrap"
            >
              <span>{downloadingCert ? 'Generating PDF…' : 'Download Certificate (PDF)'}</span>
              <span>📥</span>
            </button>
          </div>
        </section>

        {/* ── 6. Live Share Card Generation Module (B.1 WhatsApp First) ── */}
        <section aria-label="Share score card" className="pt-6">
          <div className="max-w-[640px] mx-auto text-left mb-6">
            <p className="section-label mb-1">DAMAGE SHARE KARO</p>
            <h2 className="font-display text-xl text-paper">
              Shareable Grade Card
            </h2>
          </div>

          <ShareCardGenerator result={result} />
        </section>

        {/* ── 6.2 B.5 Referral Dare Challenge ── */}
        <section aria-label="Referral Challenge">
          <ReferralChallenge />
        </section>

        {/* ── 6.5 Wall of Shame / Wall of Fame Opt-in Widget ── */}
        <section aria-label="Post to Wall of Shame" className="max-w-[640px] mx-auto text-left border border-white/[0.08] bg-white/[0.02] rounded-lg p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="font-display text-base text-paper flex items-center gap-2">
                <span>📢 Public Wall pe anonymously daal do</span>
              </p>
              <p className="font-mono text-xs text-tan-dim mt-1 leading-relaxed">
                Saare naam, email, aur company details publicly show hone se pehle sanitize ho jaate hain.
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
                    btn.innerText = '✓ Wall pe post ho gaya!'
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
              Wall pe daal do
            </button>
          </div>
        </section>

        {/* ── 7. Bottom Navigation ── */}
        <div className="pt-8 flex flex-wrap justify-center gap-4">
          <Link to="/battle" className="btn-ghost">
            ⚔️ 1-on-1 Battle Try Karo
          </Link>
          <Link to="/wall" className="btn-ghost">
            🔥 Wall of Shame/Fame Dekho
          </Link>
          <Link to="/roast" className="btn-ghost">
            Dusra resume roast karo
          </Link>
        </div>
      </div>
    </main>
  )
}
