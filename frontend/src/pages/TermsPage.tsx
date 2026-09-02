import { Link } from 'react-router-dom'

export default function TermsPage() {
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
          <p className="section-label mb-2">LEGAL &amp; COMPLIANCE</p>
          <h1 className="font-display text-3xl sm:text-4xl text-paper tracking-tight mb-3">
            Terms of Service
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            Last updated: {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </p>
        </div>

        <div className="space-y-6 font-body text-sm text-tan leading-relaxed">
          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">1. Nature of the Service</h2>
            <p>
              ResumeRoast provides automated, opinionated, AI-generated resume critiques, scoring, and suggested bullet rewrites. Feedback is intended for entertainment, educational, and professional self-improvement purposes only.
            </p>
            <p className="mt-2 font-mono text-xs text-tan-dim">
              We do not guarantee job interviews, hiring offers, or specific career outcomes resulting from the use of our grading service or rewrites.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">2. Acceptable Use</h2>
            <p>
              You agree to upload only documents that you own or have explicit authorization to submit. You must not upload files containing malware, harmful scripts, confidential trade secrets, or unauthorized personal data of third parties.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">3. Pro Billing &amp; Subscriptions</h2>
            <p>
              Paid plans are billed in advance on a recurring monthly or annual basis. You may cancel your subscription at any time through your billing settings; cancellation takes effect at the conclusion of the paid billing cycle.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">4. Limitation of Liability</h2>
            <p>
              To the fullest extent permitted by law, ResumeRoast and its creators shall not be liable for any direct, indirect, incidental, or consequential damages resulting from your use of this service.
            </p>
          </section>
        </div>
      </div>
    </main>
  )
}
