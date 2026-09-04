import React, { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAppStore } from '@/store/useAppStore'
import { loadRazorpaySDK, RazorpaySuccessResponse } from '@/utils/razorpay'

type CheckoutStatus = 'idle' | 'creating_order' | 'modal_open' | 'verifying' | 'success' | 'failed' | 'cancelled' | 'error'

interface GatewayConfig {
  provider: string
  mode: string
  simulated: boolean
  key_id: string
  currency: string
  plans: {
    monthly: { amount_paise: number; amount_inr: number; name: string }
    annual: { amount_paise: number; amount_inr: number; name: string }
  }
}

interface SimulatedOrderData {
  order_id: string
  amount: number
  currency: string
  plan: string
  plan_name: string
  message: string
}

export default function PricingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const returnUrl = searchParams.get('from') || searchParams.get('return_to') || '/roast'

  const { usage, setUsage } = useAppStore()
  const [annual, setAnnual] = useState(false)
  const [email, setEmail] = useState('')
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutStatus>('idle')
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null)
  const [gatewayConfig, setGatewayConfig] = useState<GatewayConfig | null>(null)
  const [simulatedOrder, setSimulatedOrder] = useState<SimulatedOrderData | null>(null)

  // Prepopulate email from localStorage if available
  useEffect(() => {
    try {
      const savedEmail = localStorage.getItem('resumeroast_user_email')
      if (savedEmail) {
        setEmail(savedEmail)
      }
    } catch {}

    // Fetch public gateway config for mode transparency
    axios
      .get('/api/billing/config')
      .then(({ data }) => setGatewayConfig(data))
      .catch(() => {})
  }, [])

  const comparisonRows = [
    { feature: 'Daily resume submissions', free: '1 submission / day', pro: 'Unlimited' },
    { feature: 'Flagged flaws displayed', free: 'Top 3 issues only', pro: 'Full breakdown (5–8 issues)' },
    { feature: 'Rewritten bullet replacements', free: 'Blurred preview', pro: 'Full copyable rewrites' },
    { feature: 'Strengths & elements spared', free: 'Included', pro: 'Included' },
    { feature: 'Shareable score stamp card', free: 'Included', pro: 'Included' },
    { feature: 'Official Parody PDF diploma', free: 'Watermarked', pro: 'Custom HD Pro Edition' },
    { feature: 'Priority analysis queue', free: 'Standard', pro: 'Instant priority' },
    { feature: 'Historical submissions log', free: '—', pro: 'Included' },
  ]

  const handleInitiatePayment = async (userEmail: string) => {
    const cleanEmail = userEmail.trim().toLowerCase()
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setCheckoutStatus('error')
      setCheckoutMessage('Please enter a valid email address.')
      return
    }

    try {
      localStorage.setItem('resumeroast_user_email', cleanEmail)
    } catch {}

    setCheckoutStatus('creating_order')
    setCheckoutMessage(null)
    setSimulatedOrder(null)

    try {
      // 1. Preload Razorpay Checkout JS SDK in background
      loadRazorpaySDK().catch((err) => console.warn('Preloading SDK warning:', err))

      // 2. Create server-side order with strictly validated pricing
      const selectedPlan = annual ? 'annual' : 'monthly'
      const { data } = await axios.post('/api/create-order', {
        email: cleanEmail,
        plan: selectedPlan,
      })

      // 3. Check if running in Developer Simulation Mode
      if (data.simulated) {
        setSimulatedOrder({
          order_id: data.order_id,
          amount: data.amount,
          currency: data.currency,
          plan: data.plan,
          plan_name: data.plan_name,
          message: data.message,
        })
        setCheckoutStatus('modal_open')
        return
      }

      // 4. Real Razorpay In-Page Checkout
      const isSdkLoaded = await loadRazorpaySDK()
      if (!isSdkLoaded || !window.Razorpay) {
        throw new Error('Could not initialize Razorpay SDK. Please check your internet connection or ad-blocker.')
      }

      const planName = annual ? 'Resume Roast Pro (Annual)' : 'Resume Roast Pro (Monthly)'
      const planAmount = annual ? '₹799' : '₹99'
      const razorpayKey = data.key_id || import.meta.env.VITE_RAZORPAY_KEY_ID

      const options = {
        key: razorpayKey,
        amount: data.amount,
        currency: data.currency || 'INR',
        name: 'Resume Roast',
        description: `${planName} — ${planAmount}`,
        order_id: data.order_id,
        prefill: {
          email: cleanEmail,
        },
        theme: {
          color: '#E8422D', // Resume Roast crimson stamp
        },
        modal: {
          ondismiss: () => {
            setCheckoutStatus('cancelled')
            setCheckoutMessage('Payment window was dismissed. Click below to retry whenever you are ready.')
          },
          confirm_close: true,
        },
        // Display UPI as the primary choice for Indian users
        config: {
          display: {
            blocks: {
              upi: {
                name: 'Pay with UPI (GPay, PhonePe, Paytm, QR)',
                instruments: [{ method: 'upi' }],
              },
              cards: {
                name: 'Debit & Credit Cards (Visa, Mastercard, RuPay)',
                instruments: [{ method: 'card' }],
              },
              netbanking: {
                name: 'Netbanking (All Major Indian Banks)',
                instruments: [{ method: 'netbanking' }],
              },
            },
            sequence: ['block.upi', 'block.cards', 'block.netbanking'],
            preferences: {
              show_default_blocks: true,
            },
          },
        },
        handler: async (response: RazorpaySuccessResponse) => {
          await verifyPaymentSuccess(response, cleanEmail, selectedPlan)
        },
      }

      const rzp = new window.Razorpay(options)

      rzp.on('payment.failed', (failResp: any) => {
        const desc = failResp?.error?.description || failResp?.error?.reason || 'Transaction was declined by bank or UPI app.'
        setCheckoutStatus('failed')
        setCheckoutMessage(`Payment Failed: ${desc}`)
      })

      setCheckoutStatus('modal_open')
      rzp.open()
    } catch (err: any) {
      const errorDetail = err?.response?.data?.detail
      const displayMsg =
        typeof errorDetail === 'string'
          ? errorDetail
          : errorDetail?.message || err?.message || 'Server issue initiating checkout. Please try again.'
      setCheckoutStatus('error')
      setCheckoutMessage(displayMsg)
    }
  }

  // Cryptographic or Simulation Payment Verification
  const verifyPaymentSuccess = async (
    paymentData: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string },
    userEmail: string,
    plan: string,
  ) => {
    setCheckoutStatus('verifying')
    setCheckoutMessage(null)

    try {
      const { data } = await axios.post('/api/verify-payment', {
        razorpay_order_id: paymentData.razorpay_order_id,
        razorpay_payment_id: paymentData.razorpay_payment_id,
        razorpay_signature: paymentData.razorpay_signature,
        email: userEmail,
        plan: plan,
      })

      if (data.is_pro || data.status === 'success') {
        // Unlock Pro in global client store & localStorage
        setUsage({
          used: usage?.used ?? 0,
          remaining: 999999,
          limit: 999999,
          is_pro: true,
        })

        try {
          localStorage.setItem('resumeroast_is_pro', 'true')
          localStorage.setItem('resumeroast_user_email', userEmail)
        } catch {}

        setCheckoutStatus('success')
        setCheckoutMessage(data.message || 'Payment verified successfully! Pro access is now active.')
      } else {
        throw new Error(data.message || 'Verification returned unexpected status.')
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : err?.message || 'Verification failed. Please contact support.'
      setCheckoutStatus('error')
      setCheckoutMessage(`Verification Error: ${msg}`)
    }
  }

  // Developer simulation helper for local test approval
  const handleSimulatePaymentApproval = async () => {
    if (!simulatedOrder) return
    const simPaymentId = `pay_sim_${Date.now()}`
    const simSignature = 'sim_signature_dev_approved'

    await verifyPaymentSuccess(
      {
        razorpay_order_id: simulatedOrder.order_id,
        razorpay_payment_id: simPaymentId,
        razorpay_signature: simSignature,
      },
      email,
      simulatedOrder.plan,
    )
  }

  return (
    <main className="min-h-screen pb-24">
      {/* Top Bar */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-12">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <div className="flex items-center gap-4">
            {returnUrl && returnUrl !== '/roast' && (
              <Link to={returnUrl} className="font-mono text-xs text-ember hover:underline">
                ← Back to Roast
              </Link>
            )}
            <Link to="/" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              Desk Home
            </Link>
          </div>
        </div>
      </header>

      <div className="max-w-[960px] mx-auto px-4">
        {/* Title */}
        <div className="text-center mb-12">
          <p className="section-label mb-3">HONEST PRICING // INDIA-FIRST CHECKOUT</p>
          <h1 className="font-display text-3xl sm:text-5xl text-paper tracking-tight mb-4">
            Free forever. Deep roast for Pro.
          </h1>
          <p className="font-mono text-xs text-tan-dim max-w-[540px] mx-auto leading-relaxed">
            Direct UPI, QR code, and Debit Cards. No mandatory recurring e-mandate surprises. Upgrade once and rewrite every single weak line.
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
              Monthly Pass
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                annual ? 'bg-bg text-paper border border-white/[0.08]' : 'text-tan-dim hover:text-tan'
              }`}
            >
              Annual Pass <span className="text-ember font-bold">(-30% OFF)</span>
            </button>
          </div>

          {/* Mode indicator banner (subtle diagnostic badge) */}
          {gatewayConfig?.simulated && (
            <div className="mt-4 inline-flex items-center gap-2 px-3 py-1 bg-amber-500/10 border border-amber-500/30 rounded-sm font-mono text-[11px] text-amber-400">
              <span>🛠️ Developer Simulation Mode</span>
              <span className="text-white/40">·</span>
              <span>Test UPI & Card flows without real money</span>
            </div>
          )}
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
                Check top flaws quickly with zero account signup required. 1 free roast every 24 hours.
              </p>
            </div>
            <Link to="/roast" className="btn-ghost w-full justify-center">
              Upload free resume
            </Link>
          </div>

          {/* Pro Tier */}
          <div
            className="rounded-sm p-8 bg-bg flex flex-col justify-between text-left relative shadow-2xl"
            style={{
              border: '2px solid #E8422D',
            }}
          >
            <div className="absolute -top-3 right-4 bg-[#E8422D]/[0.2] border border-stamp px-2.5 py-0.5 rounded-sm">
              <span className="font-mono text-[10px] text-stamp font-semibold uppercase tracking-wider">
                Recommended for job hunters
              </span>
            </div>

            <div>
              <p className="font-mono text-xs uppercase tracking-wider text-stamp mb-1">
                Pro Pass (UPI / Card)
              </p>
              <div className="flex items-baseline gap-1 mb-4">
                <span className="font-display text-3xl text-paper">
                  {annual ? '₹799' : '₹99'}
                </span>
                <span className="font-mono text-xs text-tan-dim">
                  {annual ? '/ year pass' : '/ month pass'}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Full-line critique, all 5–8 flagged issues, instant bullet rewrites, high-res diploma, and unlimited daily submissions.
              </p>

              {/* Supported Indian Payment Badges */}
              <div className="flex items-center gap-2 pt-2 pb-6 flex-wrap">
                <span className="font-mono text-[10px] bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded-sm text-paper">
                  ⚡ GPay / PhonePe / Paytm
                </span>
                <span className="font-mono text-[10px] bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded-sm text-paper">
                  Scan & Pay QR
                </span>
                <span className="font-mono text-[10px] bg-white/[0.05] border border-white/[0.08] px-2 py-0.5 rounded-sm text-paper">
                  RuPay / Visa / MC
                </span>
              </div>
            </div>

            <button
              id="razorpay-initiate-button"
              type="button"
              onClick={() => {
                setShowEmailModal(true)
                setCheckoutStatus('idle')
                setCheckoutMessage(null)
              }}
              className="btn-primary w-full justify-center text-sm py-3"
            >
              Unlock Pro Now ({annual ? '₹799' : '₹99'})
            </button>
          </div>
        </div>

        {/* Modal for Email & Razorpay In-Page Checkout */}
        {showEmailModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
            <div className="bg-[#14110E] border border-white/[0.12] rounded-sm p-6 sm:p-8 max-w-md w-full text-left space-y-4 relative shadow-2xl">
              <button
                type="button"
                onClick={() => {
                  setShowEmailModal(false)
                  setSimulatedOrder(null)
                }}
                className="absolute top-4 right-4 text-tan-dim hover:text-tan font-mono text-sm"
              >
                ✕
              </button>

              <div className="flex items-center gap-2">
                <span className="section-label">INDIA-FIRST CHECKOUT</span>
                <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-1.5 py-0.5 rounded-sm">
                  UPI & Cards
                </span>
              </div>

              <h2 className="font-display text-2xl text-paper">
                Unlock Pro Access
              </h2>

              <p className="font-body text-xs text-tan leading-relaxed">
                Selected: <strong className="text-paper">{annual ? 'Pro Annual Pass (₹799)' : 'Pro Monthly Pass (₹99)'}</strong>. Enter your email to open the in-page checkout modal.
              </p>

              {/* SUCCESS STATE */}
              {checkoutStatus === 'success' ? (
                <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-sm p-5 space-y-3 animate-fadeIn">
                  <div className="flex items-center gap-2 text-emerald-300 font-display text-lg font-bold">
                    <span>🎉</span>
                    <span>Pro Subscription Activated!</span>
                  </div>
                  <p className="font-mono text-xs text-tan-dim leading-relaxed">
                    {checkoutMessage || 'Your Pro pass is active. Unlimited submissions and all unlocked bullet rewrites are ready.'}
                  </p>
                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      type="button"
                      onClick={() => navigate(returnUrl)}
                      className="btn-primary w-full justify-center"
                    >
                      {returnUrl !== '/roast' ? 'Return to your Roast →' : 'Go to Resume Desk →'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowEmailModal(false)}
                      className="font-mono text-xs text-tan-dim hover:text-tan text-center pt-1"
                    >
                      Close
                    </button>
                  </div>
                </div>
              ) : simulatedOrder ? (
                /* DEVELOPER SIMULATION MODAL (When keys not configured in .env) */
                <div className="bg-amber-950/30 border border-amber-500/40 rounded-sm p-4 space-y-3 animate-fadeIn">
                  <div className="flex items-center gap-2 text-amber-300 font-mono text-xs font-bold uppercase">
                    <span>🛠️</span>
                    <span>Developer Simulation Checkout</span>
                  </div>
                  <p className="font-mono text-xs text-tan leading-relaxed">
                    Running in test simulation mode. Test the full unlock flow without actual payment:
                  </p>
                  <div className="bg-black/40 rounded-sm p-2.5 font-mono text-[11px] text-tan-dim space-y-1">
                    <div>Order ID: <span className="text-paper">{simulatedOrder.order_id}</span></div>
                    <div>Amount: <span className="text-paper">₹{simulatedOrder.amount / 100}</span> ({simulatedOrder.amount} paise)</div>
                    <div>User: <span className="text-paper">{email}</span></div>
                  </div>

                  <div className="flex gap-2 pt-1">
                    <button
                      type="button"
                      onClick={handleSimulatePaymentApproval}
                      className="btn-primary flex-1 justify-center text-xs py-2"
                    >
                      ✓ Simulate Success (Unlock Pro)
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCheckoutStatus('failed')
                        setCheckoutMessage('Simulated bank decline: Insufficient balance or user declined.')
                        setSimulatedOrder(null)
                      }}
                      className="btn-ghost text-xs py-2"
                    >
                      ✕ Simulate Decline
                    </button>
                  </div>
                </div>
              ) : (
                /* STANDARD EMAIL INPUT & CHECKOUT FORM */
                <div className="space-y-4">
                  <div>
                    <label className="block font-mono text-[11px] text-tan-dim mb-1 uppercase tracking-wider">
                      Email address for your Pro receipt & access:
                    </label>
                    <input
                      id="razorpay-email-input"
                      type="email"
                      placeholder="name@gmail.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      disabled={checkoutStatus === 'creating_order' || checkoutStatus === 'verifying'}
                      className="w-full bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-3 rounded-sm focus:outline-none focus:border-stamp disabled:opacity-50"
                      autoFocus
                    />
                  </div>

                  {/* Explicit Error Alert (Part 1 requirement: No generic masks) */}
                  {checkoutMessage && (
                    <div
                      role="alert"
                      className={`p-3 rounded-sm text-left font-mono text-xs leading-relaxed border ${
                        checkoutStatus === 'cancelled'
                          ? 'bg-amber-950/30 border-amber-500/40 text-amber-300'
                          : 'bg-[#E8422D]/[0.1] border-[#E8422D]/40 text-[#ff8170]'
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5 mb-0.5">
                        <span>{checkoutStatus === 'cancelled' ? 'ℹ' : '⚠'}</span>
                        <span>{checkoutStatus === 'cancelled' ? 'Notice' : 'Payment Notice'}</span>
                      </div>
                      <p>{checkoutMessage}</p>
                    </div>
                  )}

                  <div className="flex gap-3 pt-2">
                    <button
                      id="razorpay-pay-button"
                      type="button"
                      disabled={checkoutStatus === 'creating_order' || checkoutStatus === 'verifying'}
                      onClick={() => handleInitiatePayment(email)}
                      className="btn-primary flex-1 justify-center py-2.5 font-medium"
                    >
                      {checkoutStatus === 'creating_order' ? (
                        <span className="flex items-center gap-2">
                          <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Creating Order…
                        </span>
                      ) : checkoutStatus === 'verifying' ? (
                        <span className="flex items-center gap-2">
                          <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Verifying Access…
                        </span>
                      ) : checkoutStatus === 'failed' || checkoutStatus === 'cancelled' || checkoutStatus === 'error' ? (
                        'Retry Payment'
                      ) : (
                        `Pay ${annual ? '₹799' : '₹99'} with UPI / Card`
                      )}
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
              )}
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
