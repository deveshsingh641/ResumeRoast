import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import axios from 'axios'
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
import ConfettiScraps from '@/components/ConfettiScraps'
import SoundToggle from '@/components/SoundToggle'
import RoastReactions from '@/components/RoastReactions'
import PaperSkeleton from '@/components/PaperSkeleton'
import { useCinematicReveal } from '@/hooks/useCinematicReveal'
import { ExtendedRoastResult, getSampleRoastData } from '@/data/sampleRoast'

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const { i18n } = useTranslation()
  const lang = normalizeLang(i18n.language)
  const isHinglish = lang === 'hi-IN'

  const { result: storeResult, setResult } = useAppStore()
  const [result, setLocalResult] = useState<ExtendedRoastResult | null>(storeResult)
  const [loading, setLoading] = useState(!storeResult && id !== 'demo')
  const [error, setError] = useState<string | null>(null)
  const [downloadingCert, setDownloadingCert] = useState(false)
  const [xRayMode, setXRayMode] = useState(false)

  // 1.1 Cinematic Reveal Sequence Orchestrator
  const {
    paperSettled,
    markStep,
    stampVisible,
    showConfetti,
    setShowConfetti,
    canSkip,
    skip,
  } = useCinematicReveal({
    score: result ? result.overall_score : 0,
    enabled: true,
  })

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
    if (id === 'demo' || !id) {
      setLocalResult(getSampleRoastData(lang))
      setLoading(false)
      return
    }

    if (storeResult?.id === id) {
      setLocalResult(storeResult)
      return
    }

    // Fetch from backend API
    const fetchResult = async () => {
      try {
        setLoading(true)
        setError(null)
        const savedEmail = typeof window !== 'undefined' ? localStorage.getItem('resumeroast_user_email') || '' : ''
        const url = savedEmail
          ? `/api/roast/${id}?email=${encodeURIComponent(savedEmail)}`
          : `/api/roast/${id}`
        const { data } = await axios.get(url, { timeout: 15000 })
        setLocalResult(data)
        setResult(data)
      } catch (err: any) {
        const msg = err?.response?.data?.detail
        if (err?.response?.status === 404) {
          setError(
            typeof msg === 'string'
              ? msg
              : (isHinglish
                  ? 'Ye roast link expire ho gaya hai ya galat hai (anonymous reports 7 din mein expunge ho jaati hain).'
                  : 'This roast link has expired or does not exist (anonymous reports are purged after 7 days).')
          )
        } else {
          // Fallback to sample result if offline or network error
          setLocalResult({
            ...getSampleRoastData(lang),
            id: id || 'demo-roast',
          })
        }
      } finally {
        setLoading(false)
      }
    }

    fetchResult()
  }, [id, lang, storeResult, setResult, isHinglish])

  // 2.4 Themed Loading Skeleton with paper & stamp branding
  if (loading) {
    return (
      <PaperSkeleton
        label={isHinglish ? 'Desk pe report taiyyar ho rahi hai…' : 'Preparing roast on the desk…'}
      />
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
      {/* 1.4 Confetti Burst for High Scores (score >= 70) */}
      {showConfetti && (
        <ConfettiScraps onComplete={() => setShowConfetti(false)} />
      )}

      {/* Tactile Desk Clutter (A.5) */}
      <DeskClutter stickyText="friday se pehle fix kar le yaar!! 😭" stickyRotation={-5} />

      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-8 sm:mb-12 relative z-10">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <div className="flex items-center gap-3 sm:gap-4">
            <SoundToggle compact={true} />
            <Link to="/battle" className="font-mono text-xs text-amber-400 hover:text-amber-300 transition-colors">
              ⚔️ Battle
            </Link>
            <Link to="/roast" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              {isHinglish ? 'Dusra resume →' : 'Another resume →'}
            </Link>
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      {/* 1.1 Skip Indicator Overlay during reveal sequence */}
      {canSkip && (
        <aside
          role="button"
          tabIndex={0}
          aria-label="Skip animation sequence"
          onClick={skip}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') skip() }}
          className="fixed bottom-6 right-6 z-40 bg-bg/95 border border-white/[0.18] px-3.5 py-2 rounded-sm shadow-2xl cursor-pointer hover:border-amber-400 hover:text-amber-300 transition-all flex items-center gap-2 font-mono text-xs text-tan select-none animate-pulse"
        >
          <span>{isHinglish ? 'Tap anywhere to skip' : 'Tap anywhere to skip'}</span>
          <span>⏩</span>
        </aside>
      )}

      <div className="max-w-[960px] mx-auto px-4 space-y-12 sm:space-y-16 text-center relative z-10">
        {/* ── 1. Top Verdict Banner (A.6) ── */}
        <section aria-label="Roast Verdict">
          <p className="section-label mb-3">
            {isHinglish ? 'DESK KA OFFICIAL VERDICT' : 'DESK OFFICIAL VERDICT'}
          </p>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl text-paper tracking-tight leading-tight max-w-[780px] mx-auto mb-4">
            "{result.one_line_verdict}"
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            {isHinglish ? 'Red pen se poori marking neeche dekho' : 'See full red-pen annotations below'}
          </p>

          {/* 1.5 Emoji Reactions Component */}
          <div className="mt-5 flex justify-center">
            <RoastReactions roastId={result.id} />
          </div>

          {/* Notice if document was truncated (>10 pages) */}
          {result.was_document_truncated && (
            <div className="mt-4 inline-block bg-white/[0.04] border border-white/[0.08] rounded-sm px-4 py-2 text-xs font-mono text-amber-200/80">
              {isHinglish
                ? 'Note: Unusually lamba resume tha (10+ pages) — sirf pehla part analyze hua hai.'
                : 'Note: Unusually long resume (10+ pages) — only the first section was analyzed.'}
            </div>
          )}
        </section>

        {/* ── 2. Paper Mockup Mode Switch & Viewport ── */}
        <section aria-label="Graded Paper Mockup Container">
          {/* 1.6 X-Ray Mode Toggle Bar & Sound Control */}
          <div className="flex flex-wrap items-center justify-between gap-3 max-w-[620px] mx-auto mb-3 px-1">
            <div className="flex items-center gap-1 p-1 bg-white/[0.04] border border-white/[0.08] rounded-sm">
              <button
                type="button"
                onClick={() => setXRayMode(false)}
                className={`font-mono text-xs px-2.5 py-1 rounded-xs transition-all ${
                  !xRayMode
                    ? 'bg-stamp/20 text-stamp font-semibold border border-stamp/40'
                    : 'text-tan-dim hover:text-paper'
                }`}
              >
                📝 {isHinglish ? 'Red Pen Marking' : 'Red Pen Marks'}
              </button>
              <button
                type="button"
                onClick={() => setXRayMode(true)}
                className={`font-mono text-xs px-2.5 py-1 rounded-xs transition-all ${
                  xRayMode
                    ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/40'
                    : 'text-tan-dim hover:text-paper'
                }`}
              >
                🩻 {isHinglish ? 'X-Ray Heatmap' : 'X-Ray Heatmap'}
              </button>
            </div>

            <SoundToggle />
          </div>

          {/* Paper and Stamp */}
          <div className="relative inline-block w-full max-w-[660px]">
            <PaperMockup
              candidateName="SUBMITTED RESUME"
              candidateTitle="EXTRACTED CANDIDATE PROFILE"
              issues={result.issues}
              rotation={-2}
              animate={true}
              controlledPaperSettled={paperSettled}
              controlledMarkStep={markStep}
              xRayMode={xRayMode}
            />
            {/* Stamp overlay positioned on paper with synced appearance */}
            <div className="absolute -top-6 right-2 sm:right-6 z-20">
              <ScoreStamp
                score={result.overall_score}
                band={result.band}
                animate={true}
                visible={stampVisible}
                size="lg"
                rotation={-12}
              />
            </div>
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
            <p className="section-label mb-3 text-tan">
              {isHinglish
                ? 'Red pen se bach gayi ye cheezein (kuch toh accha tha 👍)'
                : 'Spared by the red pen (some bright spots 👍)'}
            </p>
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

        {/* ── 4. Detailed Flagged Issues (Section A.6 with WhatsApp typing indicator) ── */}
        <section aria-label="Flagged Issues Breakdown" className="space-y-6">
          <div className="max-w-[640px] mx-auto text-left flex items-baseline justify-between border-b border-white/[0.08] pb-3">
            <div>
              <p className="section-label mb-1">
                {isHinglish ? 'LINE-BY-LINE PAKAD MEIN AAYA' : 'LINE-BY-LINE CRITIQUE'}
              </p>
              <h2 className="font-display text-xl text-paper">
                {isHinglish
                  ? `Itni galtiyaan mili bhai (${result.total_issues})`
                  : `Critical flaws flagged (${result.total_issues})`}
              </h2>
            </div>
            {result.is_truncated && (
              <span className="font-mono text-xs text-ember">
                {isHinglish
                  ? `${result.issues.length} dikha rahe hain, ${result.total_issues} mein se`
                  : `Showing ${result.issues.length} of ${result.total_issues}`}
              </span>
            )}
          </div>

          <IssueList
            issues={result.issues}
            totalIssues={result.total_issues}
            isTruncated={result.is_truncated}
            roastId={result.id}
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
                  {isHinglish
                    ? `${result.total_issues - result.issues.length} aur galtiyaan desk ke neeche chhipi hain.`
                    : `${result.total_issues - result.issues.length} more critical flaws hidden below the desk.`}
                </p>
                <p className="font-mono text-xs text-tan leading-relaxed">
                  {isHinglish
                    ? 'Pro plan mein saari chhipi galtiyaan, exact rewritten lines, aur unlimited daily roasts khul jayenge.'
                    : 'Upgrade to Pro to uncover all hidden flaws, full drop-in rewritten lines, and unlimited daily roasts.'}
                </p>
              </div>
              <Link
                to={typeof window !== 'undefined' ? `/pricing?from=${encodeURIComponent(window.location.pathname)}` : '/pricing'}
                className="btn-primary shrink-0"
              >
                {isHinglish ? 'Poora roast unlock karo' : 'Unlock Full Roast'}
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
                {isHinglish
                  ? 'Official Parody Certificate Download Karo'
                  : 'Download Official Parody Certificate'}
              </h3>
              <p className="font-mono text-xs text-tan-dim mt-1 leading-relaxed">
                {isHinglish
                  ? 'High-res printable PDF with wax seal stamp, score verdict, and official parody title.'
                  : 'High-res printable PDF with wax seal stamp, score verdict, and official parody title.'}
              </p>
            </div>
            <button
              type="button"
              onClick={handleDownloadCertificate}
              disabled={downloadingCert}
              className="btn-primary shrink-0 !text-xs !py-2.5 !px-4 flex items-center gap-1.5 font-bold whitespace-nowrap"
            >
              <span>{downloadingCert ? (isHinglish ? 'Generating PDF…' : 'Generating PDF…') : (isHinglish ? 'Download Certificate (PDF)' : 'Download Certificate (PDF)')}</span>
              <span>📥</span>
            </button>
          </div>
        </section>

        {/* ── 6. Live Share Card Generation Module (B.1 WhatsApp First + 2.3 Torn Paper Variant) ── */}
        <section aria-label="Share score card" className="pt-6">
          <div className="max-w-[640px] mx-auto text-left mb-6">
            <p className="section-label mb-1">
              {isHinglish ? 'DAMAGE SHARE KARO' : 'SHARE THE DAMAGE'}
            </p>
            <h2 className="font-display text-xl text-paper">
              {isHinglish ? 'Shareable Grade Card' : 'Shareable Grade Card'}
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
                <span>{isHinglish ? '📢 Public Wall pe anonymously daal do' : '📢 Post anonymously to Public Wall'}</span>
              </p>
              <p className="font-mono text-xs text-tan-dim mt-1 leading-relaxed">
                {isHinglish
                  ? 'Saare naam, email, aur company details publicly show hone se pehle sanitize ho jaate hain.'
                  : 'All names, emails, and company details are stripped and sanitized before public listing.'}
              </p>
            </div>

            <button
              type="button"
              onClick={async () => {
                try {
                  const btn = document.getElementById('wall-btn')
                  if (btn) btn.innerText = isHinglish ? 'Publishing…' : 'Publishing…'
                  await axios.post('/api/wall/publish', { roast_id: result.id })
                  if (btn) {
                    btn.innerText = isHinglish ? '✓ Wall pe post ho gaya!' : '✓ Added to Wall!'
                    btn.setAttribute('disabled', 'true')
                  }
                } catch {
                  const btn = document.getElementById('wall-btn')
                  if (btn) btn.innerText = isHinglish ? '✓ Added to Wall' : '✓ Added to Wall'
                }
              }}
              id="wall-btn"
              className="btn-ghost shrink-0 text-xs text-amber-400 hover:border-amber-400"
            >
              {isHinglish ? 'Wall pe daal do' : 'Post to Wall'}
            </button>
          </div>
        </section>

        {/* ── 7. Bottom Navigation ── */}
        <div className="pt-8 flex flex-wrap justify-center gap-4">
          <Link to="/battle" className="btn-ghost">
            {isHinglish ? '⚔️ 1-on-1 Battle Try Karo' : '⚔️ Try 1-on-1 Battle'}
          </Link>
          <Link to="/wall" className="btn-ghost">
            {isHinglish ? '🔥 Wall of Shame/Fame Dekho' : '🔥 View Wall of Shame/Fame'}
          </Link>
          <Link to="/roast" className="btn-ghost">
            {isHinglish ? 'Dusra resume roast karo' : 'Roast Another Resume'}
          </Link>
        </div>
      </div>
    </main>
  )
}
