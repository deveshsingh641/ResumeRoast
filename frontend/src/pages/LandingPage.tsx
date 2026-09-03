import { useState } from 'react'
import { Link } from 'react-router-dom'
import ScoreStamp from '@/components/ScoreStamp'
import PaperMockup from '@/components/PaperMockup'
import DeskClutter from '@/components/DeskClutter'
import MarqueeTicker from '@/components/MarqueeTicker'
import PlacementSeasonBanner from '@/components/PlacementSeasonBanner'
import LiveRoastCounter from '@/components/LiveRoastCounter'
import { SAMPLE_ROAST_DATA, SAMPLE_RESUME_INFO } from '@/data/sampleRoast'

/* ── 4 Stats Hairline Gap Grid (Section A.6) ── */
function StatsRow() {
  const stats = [
    { value: '42,910', label: 'resumes ab tak roast ho chuke' },
    { value: '15s', label: 'roast milne mein' },
    { value: '100%', label: 'sign-up ki zaroorat nahi' },
    { value: '94%', label: 'dobara roast karayenge' },
  ]

  return (
    <div className="w-full max-w-[960px] mx-auto mt-16 px-4">
      <div className="gap-grid-1px grid-cols-2 md:grid-cols-4 rounded-sm overflow-hidden border border-white/[0.08]">
        {stats.map((stat, idx) => (
          <div
            key={idx}
            className="py-6 px-3 sm:px-4 flex flex-col items-center justify-center text-center transition-colors duration-150 hover:bg-white/[0.02]"
          >
            <div className="font-display text-[26px] sm:text-[30px] md:text-[28px] lg:text-[34px] text-paper tracking-tight leading-none mb-2.5 whitespace-nowrap select-none">
              {stat.value}
            </div>
            <div className="font-mono text-[11px] sm:text-xs text-tan-dim lowercase tracking-wide leading-relaxed max-w-[160px] mx-auto select-none">
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
  const steps = [
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
  return (
    <section id="sample" className="py-24 px-4 border-t border-white/[0.08]" aria-label="Sample roast">
      <div className="max-w-[960px] mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 mb-2">
            <p className="section-label">SAMPLE ROAST DEKH LE</p>
            <span className="font-mono text-[10px] text-tan-dim uppercase px-1.5 py-0.5 border border-white/10 rounded-[2px]">
              Live Preview
            </span>
          </div>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Asli roast kaisa dikhta hai, khud dekh le.
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2 max-w-lg mx-auto">
            Fresher candidate ka sample resume: bhare hue buzzwords, number gayab, aur standard generic lines.
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
              <span className="text-stamp font-semibold uppercase block mb-1">Desk ka Official Verdict:</span>
              <span className="text-paper text-sm font-display">"{SAMPLE_ROAST_DATA.one_line_verdict}"</span>
              <div className="mt-2">
                <Link to="/roast/demo" className="text-ember hover:underline text-[11px] inline-flex items-center gap-1">
                  Poora 6-issue breakdown aur voice note suno →
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
    { label: 'Issues dikhenge', free: 'Top 3 issues', pro: 'Saare 5–8 issues' },
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
            Free hamesha ke liye. Aur deep roast chahiye toh Pro.
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-2">
            Koi subscription ka jhol nahi. Instant access.
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
              Mahina
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                annual ? 'bg-bg text-paper border border-white/[0.08]' : 'text-tan-dim hover:text-tan'
              }`}
            >
              Saal <span className="text-ember">(-30%)</span>
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
                <span className="font-mono text-xs text-tan-dim">/ hamesha ke liye</span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Apne top flaws ka fatak se sach jaan-ne ke liye best hai.
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
              Free resume roast karo
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
                Zyada log ye lete hain
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
                  {annual ? '/ saal' : '/ mahina'}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Full-line critique, saari rewritten lines, aur unlimited daily roasts.
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
              Pro pe upgrade karo
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

function FAQSection() {
  const [openIdx, setOpenIdx] = useState<number | null>(null)

  return (
    <section className="py-24 px-4 border-t border-white/[0.08]" aria-label="Frequently Asked Questions">
      <div className="max-w-[800px] mx-auto text-left">
        <div className="text-center mb-16">
          <p className="section-label mb-2">SAWAL JAWAB</p>
          <h2 className="font-display text-2xl sm:text-3xl text-paper">
            Aamtaur pe pooche jaane wale sawaal.
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
      {/* B.4 Time-Boxed Placement Season Banner */}
      <PlacementSeasonBanner />

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
              Roast karwao
            </Link>
          </nav>
        </div>
      </header>

      {/* Marquee Ticker */}
      <MarqueeTicker />

      {/* ── Hero Section (Section A.2) ── */}
      <section className="pt-16 pb-16 px-4 text-center relative overflow-hidden">
        {/* Tactile Desk Clutter (Section A.5) */}
        <DeskClutter stickyText="friday se pehle fix kar le yaar!! 😭" stickyRotation={4} />

        <div className="max-w-[960px] mx-auto relative z-10">
          {/* B.2 Live Social Proof Counter */}
          <LiveRoastCounter />

          {/* Eyebrow Line */}
          <p className="section-label mb-4">
            DESK PE POORA SACH // 100% RAW AI ROAST
          </p>

          {/* Headline with Rotated Red Pen Strikethrough (A.2 Exact Spec) */}
          <h1 className="font-display text-4xl sm:text-6xl md:text-7xl text-paper tracking-tight leading-[0.98] mb-6">
            TERA RESUME{' '}
            <span className="red-pen-strike text-tan-dim">IMPRESSIVE</span> HAI...
            <br />
            <span className="text-stamp">BAS FLUFF HAI BHAI.</span>
          </h1>

          {/* Subcopy (A.2 Exact Spec) */}
          <p className="font-body text-base sm:text-lg text-tan max-w-[660px] mx-auto mb-8 leading-relaxed">
            Red pen se poori marking hogi, ek pakka verdict stamp milega, aur exact line likh ke bhi denge ki fix kaise karna hai.
          </p>

          {/* Primary + Ghost CTA Pair (A.2 Exact Spec) */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link to="/roast" id="hero-cta" className="btn-primary">
              Resume daal de bhai
            </Link>
            <a href="#sample" className="btn-ghost">
              Pehle sample dekh le
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
          <p className="section-label mb-3">INSTANT ROAST</p>
          <h2 className="font-display text-3xl sm:text-4xl text-paper mb-4 leading-tight">
            Apna resume desk pe rakh do.
          </h2>
          <p className="font-mono text-xs text-tan-dim mb-8">
            Free · 1 roast/day · Koi credit card nahi chahiye · ~15 seconds mein report
          </p>
          <Link to="/roast" className="btn-primary">
            Resume daal de bhai
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
              resume roast — desk kabhi jhooth nahi bolta.
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
