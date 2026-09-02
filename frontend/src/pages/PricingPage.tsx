import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

export default function PricingPage() {
  const [annual, setAnnual] = useState(false)
  const [email, setEmail] = useState('')
  const [isCheckingOut, setIsCheckingOut] = useState(false)
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)

  const comparisonRows = [
    { feature: 'Daily resume submissions', free: '1 submission / day', pro: 'Unlimited' },
    { feature: 'Flagged flaws displayed', free: 'Top 3 issues only', pro: 'Full breakdown (5–8 issues)' },
    { feature: 'Rewritten bullet replacements', free: 'Blurred preview', pro: 'Full copyable rewrites' },
    { feature: 'Strengths & elements spared', free: 'Included', pro: 'Included' },
    { feature: 'Shareable score stamp card', free: 'Included', pro: 'Included' },
    { feature: 'Priority analysis queue', free: 'Standard', pro: 'Instant priority' },
    { feature: 'Historical submissions log', free: '—', pro: 'Included' },
  ]

  const handleCheckout = async (userEmail: string) => {
    if (!userEmail || !userEmail.includes('@')) {
      setCheckoutMessage('Please enter a valid email address.')
      return
    }

    setIsCheckingOut(true)
    setCheckoutMessage(null)

    try {
      const { data } = await axios.post('/api/checkout', {
        email: userEmail,
        plan: annual ? 'annual' : 'monthly',
      })

      if (data.url) {
        window.location.href = data.url
      } else {
        setCheckoutMessage('Pro subscription activated successfully!')
        setShowEmailModal(false)
      }
    } catch {
      setCheckoutMessage('Unable to connect to payment checkout. Please try again.')
    } finally {
      setIsCheckingOut(false)
    }
  }

  return (
    <main className="min-h-screen pb-24">
      {/* Top Bar */}
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

      <div className="max-w-[960px] mx-auto px-4">
        {/* Title */}
        <div className="text-center mb-12">
          <p className="section-label mb-3">HONEST PRICING</p>
          <h1 className="font-display text-3xl sm:text-5xl text-paper tracking-tight mb-4">
            Free forever. Deep roast for Pro.
          </h1>
          <p className="font-mono text-xs text-tan-dim max-w-[500px] mx-auto leading-relaxed">
            No unexpected recurring traps. Upgrade only when you are ready to rewrite every single weak line.
          </p>

          {/* Toggle */}
          <div className="inline-flex items-center gap-4 mt-8 p-1 bg-white/[0.04] border border-white/[0.08] rounded-sm">
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

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-[800px] mx-auto mb-16">
          {/* Free Tier */}
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
                Check top flaws quickly with zero account signup required.
              </p>
            </div>
            <Link to="/roast" className="btn-ghost w-full justify-center">
              Upload free resume
            </Link>
          </div>

          {/* Pro Tier */}
          <div
            className="rounded-sm p-8 bg-bg flex flex-col justify-between text-left relative"
            style={{
              border: '2px solid #E8422D',
            }}
          >
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
                Full-line critique, all rewritten bullet suggestions, and unlimited daily submissions.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowEmailModal(true)}
              className="btn-primary w-full justify-center"
            >
              Get Pro access
            </button>
          </div>
        </div>

        {/* Modal for Email Checkout */}
        {showEmailModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
            <div className="bg-bg border border-white/[0.1] rounded-sm p-6 sm:p-8 max-w-md w-full text-left space-y-4 relative">
              <button
                type="button"
                onClick={() => setShowEmailModal(false)}
                className="absolute top-4 right-4 text-tan-dim hover:text-tan font-mono text-sm"
              >
                ✕
              </button>
              <p className="section-label">UPGRADE TO PRO</p>
              <h2 className="font-display text-2xl text-paper">
                Unlock Full Roast
              </h2>
              <p className="font-body text-xs text-tan leading-relaxed">
                Enter your email address to proceed to Stripe checkout ({annual ? '₹2,499/year' : '₹299/month'}).
              </p>
              <input
                type="email"
                placeholder="your.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-[#17140F] border border-white/[0.15] text-paper font-mono text-xs p-3 rounded-sm focus:outline-none focus:border-stamp"
                autoFocus
              />
              {checkoutMessage && (
                <p className="font-mono text-xs text-stamp">
                  {checkoutMessage}
                </p>
              )}
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  disabled={isCheckingOut}
                  onClick={() => handleCheckout(email)}
                  className="btn-primary flex-1 justify-center"
                >
                  {isCheckingOut ? 'Opening Stripe…' : 'Continue to payment'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowEmailModal(false)}
                  className="btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 1px Hairline Gap Comparison Table */}
        <div className="max-w-[800px] mx-auto text-left">
          <p className="section-label mb-3">PLAN COMPARISON</p>
          <div className="gap-grid-1px grid-cols-3 border border-white/[0.08] rounded-sm overflow-hidden font-mono text-xs">
            {/* Header row */}
            <div className="p-4 text-tan-dim uppercase">Feature</div>
            <div className="p-4 text-tan-dim uppercase text-center">Free</div>
            <div className="p-4 text-stamp uppercase text-center font-semibold">Pro</div>

            {/* Comparison items */}
            {comparisonRows.map((row, idx) => (
              <React.Fragment key={`row-${idx}`}>
                <div className="p-4 text-tan font-body text-xs">
                  {row.feature}
                </div>
                <div className="p-4 text-tan-dim text-center">
                  {row.free}
                </div>
                <div className="p-4 text-paper text-center font-medium">
                  {row.pro}
                </div>
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </main>
  )
}
