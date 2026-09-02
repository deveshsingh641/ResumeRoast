import { Link } from 'react-router-dom'

export default function PrivacyPage() {
  return (
    <main className="min-h-screen pb-24">
      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-12">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <Link to="/" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
            ← Back to Desk
          </Link>
        </div>
      </header>

      <div className="max-w-[720px] mx-auto px-4 text-left space-y-8">
        <div>
          <p className="section-label mb-2">LEGAL &amp; PRIVACY</p>
          <h1 className="font-display text-3xl sm:text-4xl text-paper tracking-tight mb-3">
            Privacy Policy
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </p>
        </div>

        <div className="space-y-6 font-body text-sm text-tan leading-relaxed">
          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">1. Document Processing &amp; Retention</h2>
            <p>
              When you upload a resume to ResumeRoast, the document text is processed in-memory solely to generate your critique, scoring, and rewritten bullet points.
            </p>
            <p className="mt-2 font-mono text-xs text-ember">
              Anonymous roast results are cached for exactly 7 days to allow you to share your link, after which all associated text and verdicts are automatically and permanently purged.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">2. What We Do NOT Do</h2>
            <ul className="list-disc pl-5 space-y-1 text-xs font-mono text-tan-dim">
              <li>We never sell, rent, or trade your resume data to recruiters, employers, or third-party brokers.</li>
              <li>We do not train public AI foundation models on your submitted resume files.</li>
              <li>We do not log personal candidate identifiers (names, addresses, phone numbers) in server access logs.</li>
            </ul>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">3. Device Fingerprinting &amp; Rate Limiting</h2>
            <p>
              To prevent abuse and manage free-tier daily usage limits, we compute an anonymous one-way hash (SHA-256) of standard request headers. This hash cannot be reverse-engineered to identify you.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">4. Payment Information</h2>
            <p>
              All payments for Pro access are processed directly by Stripe. We never store or handle your raw credit card numbers or banking credentials on our servers.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">5. Contact &amp; Data Deletion</h2>
            <p>
              If you have any questions or wish to request immediate manual deletion of any cached roast record, reach out to privacy@resumeroast.app.
            </p>
          </section>
        </div>
      </div>
    </main>
  )
}
