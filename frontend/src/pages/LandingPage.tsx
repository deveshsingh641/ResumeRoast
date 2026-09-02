import { useState } from 'react'
import { Link } from 'react-router-dom'
import ScoreStamp from '@/components/ScoreStamp'
import PaperMockup from '@/components/PaperMockup'
import DeskClutter from '@/components/DeskClutter'
import MarqueeTicker from '@/components/MarqueeTicker'
import { SAMPLE_ROAST_DATA, SAMPLE_RESUME_INFO } from '@/data/sampleRoast'

/* ── 4 Stats Hairline Gap Grid ── */
function StatsRow() {
  const stats = [
    { value: '42,910', label: 'Resumes Graded' },
    { value: '44', label: 'Average Score' },
    { value: '88%', label: 'Fluff Removed' },
    { value: '15s', label: 'Grading Time' },
  ]

  return (
    <div className="w-full max-w-[960px] mx-auto mt-16 px-4">
      <div className="gap-grid-1px grid-cols-2 md:grid-cols-4 rounded-sm overflow-hidden border border-white/[0.08]">
        {stats.map((stat, idx) => (
          <div key={idx} className="p-6 text-center">
            <div className="font-display text-2xl sm:text-3xl text-paper tracking-tight leading-none mb-2">
              {stat.value}
            </div>
            <div className="font-mono text-xs text-tan-dim uppercase tracking-wider">
              {stat.label}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── 3 Numbered Feature Rows ── */
function FeatureSection() {
  const steps = [
    {
      num: '01',
      title: 'Drop your resume onto the grading desk',
      desc: 'Submit your text-based PDF or DOCX file. Our engine parses every bullet point, section title, and metric without superficial keyword-matching tricks.',
    },
    {
      num: '02',
      title: 'Get marked with red pen annotations & a harsh score',
      desc: 'Get a stamped overall score from 0 to 100 alongside circled buzzwords, unquantified claims, formatting bloat, and embarrassing resume habits.',
    },
    {
      num: '03',
      title: 'Re-engineer every line with concrete rewrites',
      desc: 'Receive specific rewritten replacements for your weakest bullets with quantifiable metrics, active verbs, and zero corporate filler.',
    },
  ]

  return (
    <section className="py-24 px-4 border-t border-white/[0.08]" aria-label="How it works">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-16">
          <p className="section-label mb-2">Methodology</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Three steps. Zero sugarcoating.
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

/* ── Real Output Sample Roast ── */
function SampleSection() {
  return (
    <section id="sample" className="py-24 px-4 border-t border-white/[0.08]" aria-label="Sample roast">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 mb-2">
            <p className="section-label">GRADED DOCUMENT SAMPLE</p>
            <span className="font-mono text-[10px] text-tan-dim uppercase px-1.5 py-0.5 border border-white/10 rounded-[2px]">
              Sample Roast Demo
            </span>
          </div>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            What a graded resume looks like.
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2 max-w-lg mx-auto">
            Hardcoded candidate test: typical fresher resume with buzzwords, zero metrics, and standard filler.
          </p>
        </div>

        <div className="relative flex flex-col items-center justify-center">
          <PaperMockup
            candidateName={SAMPLE_RESUME_INFO.candidateName}
            candidateTitle={SAMPLE_RESUME_INFO.candidateTitle}
            companyLine={SAMPLE_RESUME_INFO.companyLine}
            bullet1Text={SAMPLE_RESUME_INFO.bullet1Text}
            bullet1Annotated={SAMPLE_RESUME_INFO.bullet1Annotated}
            bullet1Tag={SAMPLE_RESUME_INFO.bullet1Tag}
            bullet2Text={SAMPLE_RESUME_INFO.bullet2Text}
            bullet2Annotated={SAMPLE_RESUME_INFO.bullet2Annotated}
            bullet2Tag={SAMPLE_RESUME_INFO.bullet2Tag}
            bullet3Text={SAMPLE_RESUME_INFO.bullet3Text}
            bullet3Annotated={SAMPLE_RESUME_INFO.bullet3Annotated}
            bullet3Tag={SAMPLE_RESUME_INFO.bullet3Tag}
            rotation={-1.5}
            animate={false}
          />
          <div className="mt-8 flex flex-col sm:flex-row items-center gap-4 bg-[#110E0A] border border-white/[0.08] p-4 rounded-sm max-w-xl w-full">
            <ScoreStamp score={SAMPLE_ROAST_DATA.overall_score} band={SAMPLE_ROAST_DATA.band} animate={false} size="sm" rotation={-12} />
            <div className="text-left font-mono text-xs text-tan flex-1">
              <span className="text-stamp font-semibold uppercase block mb-1">Official Desk Verdict:</span>
              <span className="text-paper text-sm font-display">"{SAMPLE_ROAST_DATA.one_line_verdict}"</span>
              <div className="mt-2">
                <Link to="/roast/demo" className="text-ember hover:underline text-[11px] inline-flex items-center gap-1">
                  Inspect full 6-issue breakdown & voice note →
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
  const [annual, setAnnual] = useState(false)

  const features = [
    { label: 'Roasts per day', free: '1/day', pro: 'Unlimited' },
    { label: 'Issues displayed', free: 'Top 3 issues', pro: 'All 5–8 issues' },
    { label: 'Red-pen rewritten bullets', free: 'Preview only', pro: 'Full rewrite access' },
    { label: 'Key strength breakdown', free: 'Included', pro: 'Included' },
    { label: 'Shareable score stamp card', free: 'Included', pro: 'Included' },
    { label: 'PDF re-export recommendations', free: '—', pro: 'Included' },
  ]

  return (
    <section id="pricing" className="py-24 px-4 border-t border-white/[0.08]" aria-label="Pricing">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-12">
          <p className="section-label mb-2">Pricing</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Free forever. Deep roast for Pro.
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2">
            No subscription tricks. Instant access.
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
              Monthly
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                annual ? 'bg-bg text-paper border border-white/[0.08]' : 'text-tan-dim hover:text-tan'
              }`}
            >
              Annual <span className="text-ember">(-30%)</span>
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
                <span className="font-mono text-xs text-tan-dim">/ forever</span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Ideal for a fast, honest check of your top resume flaws.
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
              Upload free resume
            </Link>
          </div>

          {/* Pro Tier Card — with 2px stamp border & badge */}
          <div
            className="rounded-sm p-8 bg-bg flex flex-col justify-between text-left relative"
            style={{
              border: '2px solid #E8422D',
            }}
          >
            {/* Top right "most people pick this" tag */}
            <div className="absolute -top-3 right-4 bg-[#E8422D]/[0.15] border border-stamp px-2.5 py-0.5 rounded-sm">
              <span className="font-mono text-[10px] text-stamp font-semibold uppercase tracking-wider">
                Most people pick this
              </span>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-stamp mb-1">
                Pro Grading
              </p>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="font-display text-3xl text-paper">
                  {annual ? '₹2,499' : '₹299'}
                </span>
                <span className="font-mono text-xs text-tan-dim">
                  {annual ? '/ year' : '/ month'}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Full-line critique, all rewritten bullet recommendations, and unlimited submissions.
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

            {/* Single primary button in this view */}
            <Link to="/pricing" className="btn-primary w-full justify-center">
              Upgrade to Pro
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}

/* ── FAQ Accordion ── */
const FAQS = [
  {
    q: 'Does the grader actually read my entire resume?',
    a: 'Yes. Every line of text is extracted and analyzed by Claude Sonnet. Every flagged critique is directly quoted from your submitted text, not generic advice.',
  },
  {
    q: 'What file formats and sizes are supported?',
    a: 'We accept text-based PDF and DOCX files up to 5MB. Ensure your PDF has selectable text and is not a flat scanned photo.',
  },
  {
    q: 'Is my resume stored or shared with recruiters?',
    a: 'Anonymous roasts are cached for 7 days so you can share your score link, after which they are permanently expunged. We never sell your data to third parties.',
  },
  {
    q: 'Why did my resume get a score below 40?',
    a: 'A score under 40 indicates severe buzzword saturation, lack of quantifiable business results, or structural issues that get resumes filtered out by recruiters.',
  },
]

function FAQSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section className="py-24 px-4 border-t border-white/[0.08]" aria-label="Frequently Asked Questions">
      <div className="max-w-[800px] mx-auto text-left">
        <div className="text-center mb-16">
          <p className="section-label mb-2">Inquiries</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Frequently asked questions.
          </h2>
        </div>

        <div className="space-y-3">
          {FAQS.map((faq, idx) => {
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
  return (
    <main className="min-h-screen desk-cursor">
      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-4 px-6">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <nav className="flex items-center gap-4 sm:gap-6" aria-label="Main Navigation">
            <Link to="/battle" className="font-mono text-xs text-amber-400 hover:text-amber-300 transition-colors">
              ⚔️ Battle
            </Link>
            <Link to="/wall" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              🔥 Wall
            </Link>
            <a href="#sample" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors hidden sm:inline">
              Sample
            </a>
            <a href="#pricing" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors hidden sm:inline">
              Pricing
            </a>
            <Link to="/roast" className="btn-ghost btn-ghost-sm">
              Grade resume
            </Link>
          </nav>
        </div>
      </header>

      {/* Marquee Ticker */}
      <MarqueeTicker />

      {/* ── Hero Section ── */}
      <section className="pt-20 pb-16 px-4 text-center relative overflow-hidden">
        {/* Tactile Desk Clutter (Crumpled Reject, Coffee Ring Stain, Sticky Note) */}
        <DeskClutter stickyText="fix this before friday!! 😭" stickyRotation={4} />

        <div className="max-w-[960px] mx-auto relative z-10">
          {/* Eyebrow Line */}
          <p className="section-label mb-4">
            BRUTALLY HONEST AI RESUME CRITIQUE
          </p>

          {/* Headline with Rotated Red Pen Strikethrough */}
          <h1 className="font-display text-4xl sm:text-6xl md:text-7xl text-paper tracking-tight leading-[0.98] mb-6">
            YOUR RESUME IS{' '}
            <span className="red-pen-strike text-tan-dim">IMPRESSIVE</span>
            <br />
            <span className="text-stamp">FULL OF FLUFF.</span>
          </h1>

          {/* Subcopy */}
          <p className="font-body text-base sm:text-lg text-tan max-w-[620px] mx-auto mb-8 leading-relaxed">
            Get graded on the desk with red-pen annotations, an uncompromising verdict stamp, and exact bullet rewrites.
          </p>

          {/* Primary + Ghost CTA Pair */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link to="/roast" id="hero-cta" className="btn-primary">
              Upload resume
            </Link>
            <a href="#sample" className="btn-ghost">
              See sample roast
            </a>
          </div>

          {/* Hero Visual: PaperMockup + ScoreStamp */}
          <div className="relative inline-block w-full max-w-[660px]">
            <PaperMockup
              candidateName={SAMPLE_RESUME_INFO.candidateName}
              candidateTitle={SAMPLE_RESUME_INFO.candidateTitle}
              companyLine={SAMPLE_RESUME_INFO.companyLine}
              bullet1Text={SAMPLE_RESUME_INFO.bullet1Text}
              bullet1Annotated={SAMPLE_RESUME_INFO.bullet1Annotated}
              bullet1Tag={SAMPLE_RESUME_INFO.bullet1Tag}
              bullet2Text={SAMPLE_RESUME_INFO.bullet2Text}
              bullet2Annotated={SAMPLE_RESUME_INFO.bullet2Annotated}
              bullet2Tag={SAMPLE_RESUME_INFO.bullet2Tag}
              bullet3Text={SAMPLE_RESUME_INFO.bullet3Text}
              bullet3Annotated={SAMPLE_RESUME_INFO.bullet3Annotated}
              bullet3Tag={SAMPLE_RESUME_INFO.bullet3Tag}
              rotation={-2}
              animate={true}
            />

            {/* Score stamp placed on top-right of paper */}
            <div className="absolute -top-6 right-2 sm:right-6 z-20">
              <ScoreStamp score={SAMPLE_ROAST_DATA.overall_score} band={SAMPLE_ROAST_DATA.band} animate={true} size="md" rotation={-12} />
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
          <p className="section-label mb-3">Instant Evaluation</p>
          <h2 className="font-display text-3xl sm:text-4xl text-paper mb-4 leading-tight">
            Place your resume on the desk.
          </h2>
          <p className="font-mono text-xs text-tan-dim mb-8">
            Free · 1 roast/day · No credit card required · Graded in ~15 seconds
          </p>
          <Link to="/roast" className="btn-primary">
            Upload resume
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.08] py-8 px-6 text-center sm:text-left">
        <div className="max-w-[960px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="font-display text-sm text-paper">
            RESUME<span className="text-stamp">ROAST</span>
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
