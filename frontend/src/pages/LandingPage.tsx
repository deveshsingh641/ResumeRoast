import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import ScoreStamp from '@/components/ScoreStamp'
import PaperMockup from '@/components/PaperMockup'
import DeskClutter from '@/components/DeskClutter'
import MarqueeTicker from '@/components/MarqueeTicker'
import PlacementSeasonBanner from '@/components/PlacementSeasonBanner'
import LiveRoastCounter from '@/components/LiveRoastCounter'
import { getSampleResumes, getDailyRotationIndex } from '@/data/sampleRoast'

/* ── 4 Stats Hairline Gap Grid (Section A.6) ── */
function StatsRow() {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const stats = [
    { value: '42,910', label: isHinglish ? 'resumes ab tak roast ho chuke' : 'resumes roasted so far' },
    { value: '15s', label: isHinglish ? 'roast milne mein' : 'average turnaround' },
    { value: '100%', label: isHinglish ? 'sign-up ki zaroorat nahi' : 'no sign-up required' },
    { value: '94%', label: isHinglish ? 'dobara roast karayenge' : 'would roast again' },
  ]

  return (
    <div className="w-full max-w-[960px] mx-auto mt-8 sm:mt-16 px-2 sm:px-4">
      <div className="gap-grid-1px grid-cols-2 md:grid-cols-4 rounded-sm overflow-hidden border border-white/[0.08]">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="py-4 sm:py-6 px-2 sm:px-4 flex flex-col items-center justify-center text-center transition-colors duration-150 hover:bg-white/[0.02]"
          >
            <div className="font-display text-[22px] sm:text-[28px] md:text-[32px] text-paper tracking-tight leading-none mb-2 whitespace-nowrap select-none">
              {stat.value}
            </div>
            <div className="font-mono text-[10px] sm:text-xs text-tan-dim lowercase tracking-wide leading-relaxed max-w-[150px] mx-auto select-none">
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── 3 Numbered Feature Rows (Section A.6) ── */
function FeatureSection() {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const steps = isHinglish
    ? [
        {
          num: '01',
          title: 'Apna resume desk pe daal de',
          desc: 'Apna text-based PDF ya DOCX file submit karo. Koi superficial keyword matching ka jhol nahi, seedha asli bullet points, claims aur metrics check honge.',
        },
        {
          num: '02',
          title: 'Red pen se marking aur ek kadak score milega',
          desc: '0 se 100 tak ka stamped score milega, saath mein circled buzzwords, unquantified claims, formatting ka kachra aur cringe lines.',
        },
        {
          num: '03',
          title: 'Har weak line ka exact rewrite solution lo',
          desc: 'Sirf roast nahi karenge — jo bullet point bekaar hai uska exact better rewritten version likh ke denge with active verbs aur zero filler.',
        },
      ]
    : [
        {
          num: '01',
          title: 'Drop your resume on the desk',
          desc: 'Submit your standard PDF or DOCX file. No superficial keyword matching tricks — our AI deeply analyzes your actual bullet points, claims, and missing metrics.',
        },
        {
          num: '02',
          title: 'Get brutal red pen marks & a raw score',
          desc: 'Receive a stamped score from 0 to 100, alongside circled buzzwords, unquantified boasts, formatting mistakes, and cringe claims.',
        },
        {
          num: '03',
          title: 'Actionable rewrites for every single flaw',
          desc: 'We do not just roast your resume — every flagged issue comes with a drop-in rewritten bullet point using active verbs, concrete metrics, and zero filler.',
        },
      ]

  return (
    <section className="py-24 px-4 border-t border-white/[0.08]" aria-label="How it works">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-16">
          <p className="section-label mb-2">PROCESS DEKH LE</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Teen steps. Zero sugarcoating.
          </h2>
        </div>

        <div className="gap-grid-1px grid-cols-1 border border-white/[0.08] rounded-sm overflow-hidden">
          {steps.map((step) => (
            <div
              key={step.num}
              className="p-8 sm:p-10 flex flex-col md:flex-row md:items-center gap-6 md:gap-10 text-left"
            >
              <div className="font-mono text-3xl sm:text-4xl font-bold text-stamp/40 shrink-0 select-none">
                {step.num}
              </div>
              <div className="flex-1">
                <h3 className="font-body text-lg sm:text-xl font-semibold text-paper mb-2">
                  {step.title}
                </h3>
                <p className="font-body text-sm text-tan-dim leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

/* ── Real Output Sample Roast (Section A.6) ── */
function SampleSection() {
  const { i18n } = useTranslation()
  const lang = normalizeLang(i18n.language)
  const isHinglish = lang === 'hi-IN'
  const sampleList = getSampleResumes(lang)
  const [activeIdx, setActiveIdx] = useState(() => getDailyRotationIndex(sampleList))
  const sample = sampleList[activeIdx % sampleList.length]
  const { roastData, resumeInfo } = sample

  function shuffle() {
    setActiveIdx((prev) => (prev + 1) % sampleList.length)
  }

  return (
    <section id="sample" className="py-24 px-4 border-t border-white/[0.08]" aria-label="Sample roast">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 mb-2 flex-wrap justify-center">
            <p className="section-label">
              {isHinglish ? 'SAMPLE ROAST DEKH LE' : 'LIVE SAMPLE ROAST'}
            </p>
            <span className="font-mono text-[10px] text-tan-dim uppercase px-1.5 py-0.5 border border-white/10 rounded-[2px]">
              Live Preview
            </span>
            <button
              type="button"
              onClick={shuffle}
              aria-label="Show next sample resume"
              className="inline-flex items-center gap-1 font-mono text-[10px] text-tan-dim hover:text-ember px-2 py-0.5 border border-white/10 rounded-[2px] transition-colors duration-150"
            >
              <span>↻</span> {isHinglish ? 'Shuffle' : 'Shuffle'} ({(activeIdx % sampleList.length) + 1}/{sampleList.length})
            </button>
          </div>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            {isHinglish ? 'Asli roast kaisa dikhta hai, khud dekh le.' : 'See what a brutal roast actually looks like.'}
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2 max-w-lg mx-auto">
            {isHinglish
              ? `${resumeInfo.candidateName} ka resume: har ek flaw real-time mein flagged.`
              : `${resumeInfo.candidateName}'s resume: every critical flaw flagged in real time.`}
          </p>
        </div>

        <div className="relative flex flex-col items-center justify-center">
          <PaperMockup
            candidateName={resumeInfo.candidateName}
            candidateTitle={resumeInfo.candidateTitle}
            companyLine={resumeInfo.companyLine}
            bullet1Text={resumeInfo.bullet1Text}
            bullet1Annotated={resumeInfo.bullet1Annotated}
            bullet1Tag={resumeInfo.bullet1Tag}
            bullet2Text={resumeInfo.bullet2Text}
            bullet2Annotated={resumeInfo.bullet2Annotated}
            bullet2Tag={resumeInfo.bullet2Tag}
            bullet3Text={resumeInfo.bullet3Text}
            bullet3Annotated={resumeInfo.bullet3Annotated}
            bullet3Tag={resumeInfo.bullet3Tag}
            rotation={-1.5}
            animate={false}
          />
          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4 bg-[#110E0A] border border-white/[0.08] p-4 rounded-sm max-w-xl w-full">
            <ScoreStamp score={roastData.overall_score} band={roastData.band} animate={false} size="sm" rotation={-12} />
            <div className="text-left font-mono text-xs text-tan flex-1">
              <span className="text-stamp font-semibold uppercase block mb-1">
                {isHinglish ? 'Desk ka Official Verdict:' : 'Desk Official Verdict:'}
              </span>
              <span className="text-paper text-sm font-display">"{roastData.one_line_verdict}"</span>
              <div className="mt-2">
                <Link to="/roast/demo" className="text-ember hover:underline text-[11px] inline-flex items-center gap-1">
                  {isHinglish
                    ? 'Poora 6-issue breakdown aur voice note suno →'
                    : 'Listen to full voice note & 6-issue breakdown →'}
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── Pricing ── */
function PricingSection() {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const [annual, setAnnual] = useState(false)

  const features = isHinglish
    ? [
        { label: 'Roasts per day', free: '1/day', pro: 'Unlimited' },
        { label: 'Issues dikhenge', free: 'Top 3 issues', pro: 'Saare 5–8 issues' },
        { label: 'Red-pen rewritten lines', free: 'Preview only', pro: 'Full rewrite access' },
        { label: 'Key strength breakdown', free: 'Included', pro: 'Included' },
        { label: 'Shareable score stamp card', free: 'Included', pro: 'Included' },
        { label: 'PDF re-export suggestions', free: '—', pro: 'Included' },
      ]
    : [
        { label: 'Roasts per day', free: '1/day', pro: 'Unlimited' },
        { label: 'Issues displayed', free: 'Top 3 issues', pro: 'All 5–8 issues' },
        { label: 'Red-pen rewritten lines', free: 'Preview only', pro: 'Full rewrite access' },
        { label: 'Key strength breakdown', free: 'Included', pro: 'Included' },
        { label: 'Shareable score stamp card', free: 'Included', pro: 'Included' },
        { label: 'PDF re-export suggestions', free: '—', pro: 'Included' },
      ]

  return (
    <section id="pricing" className="py-24 px-4 border-t border-white/[0.08]" aria-label="Pricing">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-12">
          <p className="section-label mb-2">PRICING</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            {isHinglish ? 'Free hamesha ke liye. Aur deep roast chahiye toh Pro.' : 'Free forever. Go Pro for deep, uncensored critiques.'}
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2">
            {isHinglish ? 'Koi subscription ka jhol nahi. Instant access.' : 'No hidden fees. Instant access.'}
          </p>

          {/* Billing Switch */}
          <div className="inline-flex items-center gap-4 mt-6 p-1 bg-white/[0.04] border border-white/[0.08] rounded-sm">
            <button
              type="button"
              onClick={() => setAnnual(false)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                !annual ? 'bg-bg text-paper border border-white/[0.08]' : 'text-tan-dim hover:text-tan'
              }`}
            >
              {isHinglish ? 'Mahina' : 'Monthly'}
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                annual ? 'bg-bg text-paper border border-white/[0.08]' : 'text-tan-dim hover:text-tan'
              }`}
            >
              {isHinglish ? 'Saal' : 'Annual'} <span className="text-ember">(-33%)</span>
            </button>
          </div>
        </div>

        {/* 2-Card Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-[800px] mx-auto">
          {/* Free Tier Card */}
          <div className="border border-white/[0.08] rounded-sm p-8 bg-bg flex flex-col justify-between text-left">
            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-tan-dim mb-1">
                Standard Desk
              </p>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="font-display text-3xl text-paper">₹0</span>
                <span className="font-mono text-xs text-tan-dim">
                  {isHinglish ? '/ hamesha ke liye' : '/ forever'}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                {isHinglish
                  ? 'Apne top flaws ka fatak se sach jaan-ne ke liye best hai.'
                  : 'Perfect for uncovering your most glaring resume flaws quickly.'}
              </p>

              <ul className="space-y-3 font-mono text-xs text-tan border-t border-white/[0.08] pt-6 mb-8">
                {features.map((f, i) => (
                  <li key={i} className="flex items-center justify-between gap-2">
                    <span className="text-tan-dim">{f.label}</span>
                    <span className="text-paper font-medium">{f.free}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Link to="/roast" className="btn-ghost w-full justify-center">
              {isHinglish ? 'Free resume roast karo' : 'Roast resume for free'}
            </Link>
          </div>

          {/* Pro Tier Card */}
          <div
            className="rounded-sm p-8 bg-bg flex flex-col justify-between text-left relative"
            style={{
              border: '2px solid #E8422D',
            }}
          >
            <div className="absolute -top-3 right-4 bg-[#E8422D]/[0.15] border border-stamp px-2.5 py-0.5 rounded-sm">
              <span className="font-mono text-[10px] text-stamp font-semibold uppercase tracking-wider">
                {isHinglish ? 'Zyada log ye lete hain' : 'Most Popular'}
              </span>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-stamp mb-1">
                Pro Grading
              </p>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="font-display text-3xl text-paper">
                  {annual ? '₹799' : '₹99'}
                </span>
                <span className="font-mono text-xs text-tan-dim">
                  {annual ? (isHinglish ? '/ saal' : '/ year') : (isHinglish ? '/ mahina' : '/ month')}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                {isHinglish
                  ? 'Full-line critique, saari rewritten lines, aur unlimited daily roasts.'
                  : 'Full-line critique, all rewritten bullet points, and unlimited daily roasts.'}
              </p>

              <ul className="space-y-3 font-mono text-xs text-tan border-t border-white/[0.08] pt-6 mb-8">
                {features.map((f, i) => (
                  <li key={i} className="flex items-center justify-between gap-2">
                    <span className="text-tan-dim">{f.label}</span>
                    <span className="text-ember font-medium">{f.pro}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Link to="/pricing" className="btn-primary w-full justify-center">
              {isHinglish ? 'Pro pe upgrade karo' : 'Upgrade to Pro'}
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── FAQ Accordion ── */
const FAQS_HINGLISH = [
  {
    q: 'Kya AI sach mein mera poora resume padhta hai?',
    a: 'Haan bhai. Har ek line extract karke analyze hoti hai. Saare flagged comments directly tumhare text se quote honge, koi generic gyaan nahi.',
  },
  {
    q: 'Kaunse formats aur size supported hain?',
    a: 'PDF aur DOCX files up to 5MB. Make sure PDF selectable text ho, scanned photo nahi.',
  },
  {
    q: 'Kya mera resume kisi recruiter ke saath share hoga?',
    a: 'Bilkul nahi. Anonymous roasts 7 din baad permanently delete ho jaate hain. Hum data kisi third-party ko nahi bechte.',
  },
  {
    q: 'Mera score 40 se kam kyu aaya bhai?',
    a: 'Agar score 40 se kam hai toh iska matlab buzzwords bohot zyada hain, number gayab hain, ya formatting aisi hai jo recruiter ko 5 second mein reject karne pe majboor karti hai.',
  },
]

const FAQS_ENGLISH = [
  {
    q: 'Does the AI actually read my entire resume?',
    a: 'Yes. Every line is extracted and analyzed. All flagged critiques quote directly from your text — no generic advice.',
  },
  {
    q: 'Which file formats and sizes are supported?',
    a: 'PDF and DOCX files up to 5MB. Please ensure your PDF contains selectable text, not scanned images.',
  },
  {
    q: 'Is my resume shared with recruiters or third parties?',
    a: 'Never. Anonymous roasts are permanently purged after 7 days. We do not sell your personal data.',
  },
  {
    q: 'Why did my resume score below 40?',
    a: 'A score under 40 indicates dense buzzwords, missing impact metrics, or structure that triggers instant recruiter rejections.',
  },
]

function FAQSection() {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const faqs = isHinglish ? FAQS_HINGLISH : FAQS_ENGLISH
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section className="py-24 px-4 border-t border-white/[0.08]" aria-label="Frequently Asked Questions">
      <div className="max-w-[800px] mx-auto text-left">
        <div className="text-center mb-16">
          <p className="section-label mb-2">
            {isHinglish ? 'SAWAL JAWAB' : 'FREQUENTLY ASKED'}
          </p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            {isHinglish ? 'Aamtaur pe pooche jaane wale sawaal.' : 'Straight answers to common questions.'}
          </h2>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => {
            const isOpen = openIdx === idx
            return (
              <div
                key={idx}
                className="border border-white/[0.08] rounded-sm bg-bg overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setOpenIdx(isOpen ? null : idx)}
                  className="w-full p-5 text-left flex items-center justify-between gap-4 font-body text-sm font-medium text-paper hover:bg-white/[0.02] transition-colors"
                  aria-expanded={isOpen}
                >
                  <span>{faq.q}</span>
                  <span className="font-mono text-tan-dim select-none">
                    {isOpen ? '−' : '+'}
                  </span>
                </button>
                {isOpen && (
                  <div className="px-5 pb-5 font-mono text-xs text-tan-dim leading-relaxed border-t border-white/[0.04] pt-3">
                    {faq.a}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

/* ── Main Landing Page ── */
export default function LandingPage() {
  const { i18n } = useTranslation()
  const lang = normalizeLang(i18n.language)
  const isHinglish = lang === 'hi-IN'
  const sampleList = getSampleResumes(lang)
  const heroSample = sampleList[0]

  return (
    <main className="min-h-screen desk-cursor">
      {/* B.4 Time-Boxed Placement Season Banner */}
      <PlacementSeasonBanner />

      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-3 sm:py-4 px-3 sm:px-6">
        <div className="max-w-[960px] mx-auto flex items-center justify-between gap-2">
          <Link to="/" className="font-display text-base sm:text-lg tracking-tight text-paper select-none shrink-0">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-6">
            <nav className="flex items-center gap-2 sm:gap-5" aria-label="Main Navigation">
              <Link to="/battle" className="font-mono text-[11px] sm:text-xs text-amber-400 hover:text-amber-300 transition-colors whitespace-nowrap">
                ⚔️ <span className="hidden sm:inline">Battle</span>
              </Link>
              <Link to="/wall" className="font-mono text-[11px] sm:text-xs text-tan-dim hover:text-tan transition-colors whitespace-nowrap">
                🔥 <span className="hidden sm:inline">Wall</span>
              </Link>
              <a href="#sample" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors hidden md:inline">
                {isHinglish ? 'Sample' : 'Sample'}
              </a>
              <a href="#pricing" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors hidden md:inline">
                {isHinglish ? 'Pricing' : 'Pricing'}
              </a>
              <Link to="/roast" className="btn-ghost btn-ghost-sm !py-1 !px-2.5 sm:!px-4 text-[11px] sm:text-xs shrink-0">
                {isHinglish ? 'Roast' : 'Roast'}
              </Link>
            </nav>
            <LanguageSwitcher compact={true} className="shrink-0" />
          </div>
        </div>
      </header>

      {/* Marquee Ticker */}
      <MarqueeTicker />

      {/* ── Hero Section (Section A.2) ── */}
      <section className="pt-8 pb-10 sm:pt-16 sm:pb-16 px-3 sm:px-4 text-center relative overflow-hidden">
        {/* Tactile Desk Clutter (Section A.5 - Desktop only) */}
        <DeskClutter
          stickyText={isHinglish ? 'friday se pehle fix kar le yaar!! 😭' : 'fix this before Monday please!! 😭'}
          stickyRotation={4}
        />

        <div className="max-w-[960px] mx-auto relative z-10">
          {/* B.2 Live Social Proof Counter */}
          <LiveRoastCounter />

          {/* Eyebrow Line */}
          <p className="section-label mb-3 sm:mb-4 text-[11px] sm:text-xs">
            {isHinglish ? 'DESK PE POORA SACH // 100% RAW AI ROAST' : 'THE UNFILTERED TRUTH // 100% RAW AI ROAST'}
          </p>

          {/* Headline with Rotated Red Pen Strikethrough (A.2 Exact Spec) */}
          {isHinglish ? (
            <h1 className="font-display text-[clamp(1.75rem,5.2vw+0.25rem,4.25rem)] text-paper tracking-tight leading-[1.02] mb-4 sm:mb-6">
              TERA RESUME{' '}
              <span className="red-pen-strike text-tan-dim">IMPRESSIVE</span> HAI...
              <br />
              <span className="text-stamp">BAS FLUFF HAI BHAI.</span>
            </h1>
          ) : (
            <h1 className="font-display text-[clamp(1.75rem,5.2vw+0.25rem,4.25rem)] text-paper tracking-tight leading-[1.02] mb-4 sm:mb-6">
              YOUR RESUME LOOKS{' '}
              <span className="red-pen-strike text-tan-dim">IMPRESSIVE</span>...
              <br />
              <span className="text-stamp">UNTIL SOMEONE READS IT.</span>
            </h1>
          )}

          {/* Subcopy (A.2 Exact Spec) */}
          <p className="font-body text-sm sm:text-base md:text-lg text-tan max-w-[660px] mx-auto mb-6 sm:mb-8 leading-relaxed px-1">
            {isHinglish
              ? 'Red pen se poori marking hogi, ek pakka verdict stamp milega, aur exact line likh ke bhi denge ki fix kaise karna hai.'
              : 'Brutal red pen annotations, a definitive score stamp, and exact rewrite replacements with metrics and zero fluff.'}
          </p>

          {/* Primary + Ghost CTA Pair (A.2 Exact Spec) */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4 mb-8 sm:mb-14 w-full px-2">
            <Link to="/roast" id="hero-cta" className="btn-primary w-full sm:w-auto text-center justify-center">
              {isHinglish ? 'Resume daal de bhai' : 'Roast My Resume'}
            </Link>
            <a href="#sample" className="btn-ghost w-full sm:w-auto text-center justify-center">
              {isHinglish ? 'Pehle sample dekh le' : 'View Sample Roast'}
            </a>
          </div>

          {/* Hero Visual: PaperMockup + ScoreStamp */}
          <div className="relative inline-block w-full max-w-[640px] px-1 sm:px-0">
            <PaperMockup
              candidateName={heroSample.resumeInfo.candidateName}
              candidateTitle={heroSample.resumeInfo.candidateTitle}
              companyLine={heroSample.resumeInfo.companyLine}
              bullet1Text={heroSample.resumeInfo.bullet1Text}
              bullet1Annotated={heroSample.resumeInfo.bullet1Annotated}
              bullet1Tag={heroSample.resumeInfo.bullet1Tag}
              bullet2Text={heroSample.resumeInfo.bullet2Text}
              bullet2Annotated={heroSample.resumeInfo.bullet2Annotated}
              bullet2Tag={heroSample.resumeInfo.bullet2Tag}
              bullet3Text={heroSample.resumeInfo.bullet3Text}
              bullet3Annotated={heroSample.resumeInfo.bullet3Annotated}
              bullet3Tag={heroSample.resumeInfo.bullet3Tag}
              rotation={-2}
              animate={true}
            />

            {/* Score stamp placed on top-right of paper */}
            <div className="absolute -top-4 right-1 sm:-top-6 sm:right-6 z-20 pointer-events-none">
              <div className="block sm:hidden">
                <ScoreStamp
                  score={heroSample.roastData.overall_score}
                  band={heroSample.roastData.band}
                  animate={true}
                  size="sm"
                  rotation={-10}
                />
              </div>
              <div className="hidden sm:block">
                <ScoreStamp
                  score={heroSample.roastData.overall_score}
                  band={heroSample.roastData.band}
                  animate={true}
                  size="md"
                  rotation={-12}
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats Row ── */}
      <StatsRow />

      {/* ── Features ── */}
      <FeatureSection />

      {/* ── Sample Roast ── */}
      <SampleSection />

      {/* ── Pricing ── */}
      <PricingSection />

      {/* ── FAQ ── */}
      <FAQSection />

      {/* ── Bottom CTA ── */}
      <section className="py-24 px-4 border-t border-white/[0.08] text-center">
        <div className="max-w-[640px] mx-auto">
          <p className="section-label mb-3">INSTANT ROAST</p>
          <h2 className="font-display text-3xl sm:text-4xl text-paper mb-4 leading-tight">
            {isHinglish ? 'Apna resume desk pe rakh do.' : 'Drop your resume on the desk.'}
          </h2>
          <p className="font-mono text-xs text-tan-dim mb-8">
            {isHinglish
              ? 'Free · 1 roast/day · Koi credit card nahi chahiye · ~15 seconds mein report'
              : 'Free · 1 roast/day · No credit card required · Report ready in ~15 seconds'}
          </p>
          <Link to="/roast" className="btn-primary">
            {isHinglish ? 'Resume daal de bhai' : 'Roast My Resume Now'}
          </Link>
        </div>
      </section>

      {/* ── Footer (Section A.6 Tagline) ── */}
      <footer className="border-t border-white/[0.08] py-8 px-6 text-center sm:text-left">
        <div className="max-w-[960px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <div className="font-display text-sm text-paper">
              RESUME<span className="text-stamp">ROAST</span>
            </div>
            <p className="font-mono text-[11px] text-tan-dim mt-1">
              {isHinglish
                ? 'resume roast — desk kabhi jhooth nahi bolta.'
                : 'resume roast — the desk never lies.'}
            </p>
          </div>
          <nav className="flex items-center gap-4 font-mono text-xs text-tan-dim" aria-label="Legal footer links">
            <Link to="/pricing" className="hover:text-tan transition-colors">Pricing</Link>
            <Link to="/privacy" className="hover:text-tan transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-tan transition-colors">Terms of Service</Link>
          </nav>
          <div className="font-mono text-xs text-tan-dim">
            © {new Date().getFullYear()} ResumeRoast
          </div>
        </div>
      </footer>
    </main>
  )
}
