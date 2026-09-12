import React, { useState, useEffect, useRef } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import axios from "axios";
import { useAppStore } from "@/store/useAppStore";
import { loadRazorpaySDK, RazorpaySuccessResponse } from "@/utils/razorpay";
import WaitlistModal from "@/components/WaitlistModal";
import { usePageTitle } from "@/utils/usePageTitle";

type CheckoutStatus =
  | "idle"
  | "creating_order"
  | "modal_open"
  | "verifying"
  | "success"
  | "failed"
  | "cancelled"
  | "error";

interface GatewayConfig {
  provider: string;
  mode: string;
  simulated: boolean;
  key_id: string;
  currency: string;
  plans: {
    monthly: { amount_paise: number; amount_inr: number; name: string };
    annual: { amount_paise: number; amount_inr: number; name: string };
  };
  key_configured: boolean;
}

interface SimulatedOrderData {
  order_id: string;
  amount: number;
  currency: string;
  plan: string;
  plan_name: string;
  message: string;
}

export default function PricingPage() {
  usePageTitle("Pro Pass & VIP Waitlist");
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const returnUrl =
    searchParams.get("from") || searchParams.get("return_to") || "/roast";

  // Admin/Internal Test Gate: Keep real payment flow testable via ?test_checkout=true or /admin/checkout-test
  const isTestMode =
    searchParams.get("test_checkout") === "true" ||
    (typeof window !== "undefined" &&
      window.location.pathname.includes("/admin/checkout-test"));
  // Pro Checkout is active now that Razorpay KYC is approved (set VITE_PRO_LAUNCHING_SOON=true to re-enable waitlist)
  const isLaunchingSoon =
    import.meta.env.VITE_PRO_LAUNCHING_SOON === "true" && !isTestMode;

  const { usage, setUsage } = useAppStore();
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const [annual, setAnnual] = useState(false);
  const [email, setEmail] = useState("");
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutStatus>("idle");
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);
  const [gatewayConfig, setGatewayConfig] = useState<GatewayConfig | null>(
    null,
  );
  const [simulatedOrder, setSimulatedOrder] =
    useState<SimulatedOrderData | null>(null);
  const [showManualUpi, setShowManualUpi] = useState(false);
  const [manualUtr, setManualUtr] = useState("");
  const [manualSubmitted, setManualSubmitted] = useState(false);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualError, setManualError] = useState<string | null>(null);
  const [loadingStage, setLoadingStage] = useState<
    "immediate" | "waiting" | "timeout"
  >("immediate");

  const slowNoticeTimerRef = useRef<number | null>(null);
  const timeoutTimerRef = useRef<number | null>(null);

  const clearTimers = () => {
    if (slowNoticeTimerRef.current !== null) {
      window.clearTimeout(slowNoticeTimerRef.current);
      slowNoticeTimerRef.current = null;
    }
    if (timeoutTimerRef.current !== null) {
      window.clearTimeout(timeoutTimerRef.current);
      timeoutTimerRef.current = null;
    }
  };

  useEffect(() => {
    return () => {
      clearTimers();
    };
  }, []);

  // Escape key closes modals
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowEmailModal(false);
        setShowWaitlistModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Inline waitlist state
  const [inlineWaitlistEmail, setInlineWaitlistEmail] = useState("");
  const [inlineWaitlistLoading, setInlineWaitlistLoading] = useState(false);
  const [inlineWaitlistStatus, setInlineWaitlistStatus] = useState<
    "idle" | "success" | "already_joined" | "error"
  >("idle");
  const [inlineWaitlistMessage, setInlineWaitlistMessage] = useState<
    string | null
  >(null);

  const handleInlineWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanEmail = (inlineWaitlistEmail || email).trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@") || !cleanEmail.includes(".")) {
      setInlineWaitlistStatus("error");
      setInlineWaitlistMessage("Please enter a valid email address.");
      return;
    }

    try {
      setInlineWaitlistLoading(true);
      setInlineWaitlistStatus("idle");
      setInlineWaitlistMessage(null);

      try {
        localStorage.setItem("resumeroast_user_email", cleanEmail);
      } catch {}

      let userId: string | undefined = undefined;
      try {
        const storedId = localStorage.getItem("resumeroast_user_id");
        if (storedId) userId = storedId;
      } catch {}

      const { data } = await axios.post("/api/waitlist/join", {
        email: cleanEmail,
        source: "pricing_inline",
        user_id: userId,
      });

      if (data.is_already_on_list || data.status === "already_joined") {
        setInlineWaitlistStatus("already_joined");
        setInlineWaitlistMessage(
          data.message ||
            "You're already on the list! We'll email you the second Pro is live 🎉",
        );
      } else {
        setInlineWaitlistStatus("success");
        setInlineWaitlistMessage(
          data.message ||
            "You're on the list — we'll email you the second Pro is live 🎉",
        );
      }
    } catch (err: any) {
      setInlineWaitlistStatus("error");
      setInlineWaitlistMessage(
        err?.response?.data?.detail ||
          "Failed to join waitlist. Please try again.",
      );
    } finally {
      setInlineWaitlistLoading(false);
    }
  };

  const handleManualSubmit = async () => {
    if (!email || !email.includes("@")) {
      setManualError("Please enter a valid email address first.");
      return;
    }
    if (manualUtr.trim().length < 6) {
      setManualError("Please enter a valid UPI transaction reference (UTR).");
      return;
    }
    try {
      setManualLoading(true);
      setManualError(null);
      await axios.post("/api/payment/manual-request", {
        email: email.trim().toLowerCase(),
        plan: annual ? "annual" : "monthly",
        utr: manualUtr.trim(),
      });
      setManualSubmitted(true);
    } catch (err: any) {
      setManualError(
        err?.response?.data?.detail ||
          "Failed to record manual transfer. Please check details.",
      );
    } finally {
      setManualLoading(false);
    }
  };

  // Prepopulate email from localStorage if available
  useEffect(() => {
    try {
      const savedEmail = localStorage.getItem("resumeroast_user_email");
      if (savedEmail) {
        setEmail(savedEmail);
        setInlineWaitlistEmail(savedEmail);
      }
    } catch {}

    if (searchParams.get("waitlist") === "true") {
      setShowWaitlistModal(true);
    }
    if (
      searchParams.get("checkout") === "true" ||
      searchParams.get("pay") === "true"
    ) {
      setShowEmailModal(true);
    }

    // Pre-warm Razorpay SDK and fetch public gateway config
    loadRazorpaySDK().catch(() => {});
    axios
      .get("/api/billing/config")
      .then(({ data }) => setGatewayConfig(data))
      .catch(() => {});
  }, [searchParams]);

  const comparisonRows = [
    {
      feature: "Daily resume submissions",
      free: "1 submission / day",
      pro: "Unlimited",
    },
    {
      feature: "Flagged flaws displayed",
      free: "Top 3 issues only",
      pro: "Full breakdown (5–8 issues)",
    },
    {
      feature: "Rewritten bullet replacements",
      free: "Blurred preview",
      pro: "Full copyable rewrites",
    },
    {
      feature: "Strengths & elements spared",
      free: "Included",
      pro: "Included",
    },
    {
      feature: "Shareable score stamp card",
      free: "Included",
      pro: "Included",
    },
    {
      feature: "Official Parody PDF diploma",
      free: "Watermarked",
      pro: "Custom HD Pro Edition",
    },
    {
      feature: "Priority analysis queue",
      free: "Standard",
      pro: "Instant priority",
    },
    { feature: "Historical submissions log", free: "—", pro: "Included" },
  ];

  const reportPaymentFailure = async (
    userEmail: string,
    stage: string,
    errorMessage: string,
    orderId?: string,
  ) => {
    try {
      await axios.post("/api/payment/log-failure", {
        email: userEmail,
        stage,
        error_message: errorMessage,
        order_id: orderId,
        plan: annual ? "annual" : "monthly",
        user_agent:
          typeof navigator !== "undefined" ? navigator.userAgent : "browser",
      });
    } catch {}
  };

  const handleInitiatePayment = async (userEmail: string) => {
    const cleanEmail = userEmail.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@") || !cleanEmail.includes(".")) {
      setCheckoutStatus("error");
      setCheckoutMessage("Please enter a valid email address.");
      return;
    }

    try {
      localStorage.setItem("resumeroast_user_email", cleanEmail);
    } catch {}

    const isRetry =
      checkoutStatus === "error" ||
      checkoutStatus === "failed" ||
      checkoutStatus === "cancelled";

    clearTimers();
    setCheckoutStatus("creating_order");
    setCheckoutMessage(null);
    setSimulatedOrder(null);
    setLoadingStage("immediate");

    const tStart = performance.now();
    console.info(
      `[Razorpay PricingPage] 1. Initiating order for ${cleanEmail} (${annual ? "annual" : "monthly"}, retry=${isRetry})...`,
    );

    // Phase 2: After 3.2s, notify user that extra time is needed
    slowNoticeTimerRef.current = window.setTimeout(() => {
      setLoadingStage("waiting");
    }, 3200);

    // Phase 3: Client-side timeout guard ONLY while creating order
    timeoutTimerRef.current = window.setTimeout(() => {
      setCheckoutStatus((current) => {
        if (current === "creating_order") {
          console.warn(
            "[Razorpay PricingPage] Order creation timed out after 12s.",
          );
          setLoadingStage("timeout");
          const msg =
            "Payment server connection timed out. Please check your network and try again.";
          setCheckoutMessage(msg);
          reportPaymentFailure(cleanEmail, "order_creation_timeout", msg);
          return "error";
        }
        return current;
      });
    }, 12000);

    let activeOrderId: string | undefined = undefined;

    try {
      // 1. Preload Razorpay Checkout JS SDK in background
      loadRazorpaySDK().catch((err) =>
        console.warn("Preloading SDK warning:", err),
      );

      // 2. Create server-side order with strictly validated pricing
      const selectedPlan = annual ? "annual" : "monthly";
      const { data } = await axios.post("/api/create-order", {
        email: cleanEmail,
        plan: selectedPlan,
        force_fresh: isRetry,
      });

      activeOrderId = data.order_id;
      const tOrder = performance.now();
      console.info(
        `[Razorpay PricingPage] 2. Server order created in ${(tOrder - tStart).toFixed(0)}ms:`,
        data.order_id,
      );

      // 3. Check if running in Developer Simulation Mode
      if (data.simulated) {
        clearTimers();
        setSimulatedOrder({
          order_id: data.order_id,
          amount: data.amount,
          currency: data.currency,
          plan: data.plan,
          plan_name: data.plan_name,
          message: data.message,
        });
        setCheckoutStatus("modal_open");
        return;
      }

      // 4. Real Razorpay In-Page Checkout
      const isSdkLoaded = await loadRazorpaySDK();
      if (!isSdkLoaded || !window.Razorpay) {
        clearTimers();
        const sdkErr =
          "Could not initialize Razorpay SDK. Please check your internet connection or ad-blocker.";
        reportPaymentFailure(
          cleanEmail,
          "sdk_load_failed",
          sdkErr,
          activeOrderId,
        );
        throw new Error(sdkErr);
      }

      const planName = annual
        ? "Resume Roast Pro (Annual)"
        : "Resume Roast Pro (Monthly)";
      const planAmount = annual ? "₹799" : "₹99";
      const razorpayKey = data.key_id || import.meta.env.VITE_RAZORPAY_KEY_ID;

      const options = {
        key: razorpayKey,
        amount: data.amount,
        currency: data.currency || "INR",
        name: "Resume Roast",
        description: `${planName} — ${planAmount}`,
        order_id: data.order_id,
        prefill: {
          email: cleanEmail,
        },
        theme: {
          color: "#E8422D", // Resume Roast crimson stamp
        },
        modal: {
          ondismiss: () => {
            clearTimers();
            console.info("[Razorpay PricingPage] Modal dismissed by user.");
            setCheckoutStatus("cancelled");
            setCheckoutMessage(
              "Payment window was dismissed. Click below to retry whenever you are ready.",
            );
          },
          confirm_close: true,
        },
        handler: async (response: RazorpaySuccessResponse) => {
          clearTimers();
          const tPaid = performance.now();
          console.info(
            `[Razorpay PricingPage] Payment authorized in ${(tPaid - tStart).toFixed(0)}ms total. Verifying signature...`,
          );
          await verifyPaymentSuccess(response, cleanEmail, selectedPlan);
        },
      };

      const rzp = new window.Razorpay(options);

      rzp.on("payment.failed", (failResp: any) => {
        clearTimers();
        const desc =
          failResp?.error?.description ||
          failResp?.error?.reason ||
          "Transaction was declined by bank or UPI app.";
        console.warn("[Razorpay PricingPage] Payment failed:", failResp);
        setCheckoutStatus("failed");
        setCheckoutMessage(`Payment failed: ${desc}. No amount was deducted.`);
        reportPaymentFailure(cleanEmail, "payment_failed", desc, activeOrderId);
      });

      // Clear order-creation timers before invoking checkout overlay
      clearTimers();
      setCheckoutStatus("modal_open");
      const tOpen = performance.now();
      console.info(
        `[Razorpay PricingPage] 3. Invoking rzp.open() at +${(tOpen - tStart).toFixed(0)}ms`,
      );

      try {
        rzp.open();
      } catch (openErr: any) {
        console.error("[Razorpay PricingPage] rzp.open() error:", openErr);
        setCheckoutStatus("error");
        const openMsg =
          "Payment checkout window could not open. Please disable any pop-up/ad blockers and try again.";
        setCheckoutMessage(openMsg);
        reportPaymentFailure(
          cleanEmail,
          "overlay_open_error",
          openMsg,
          activeOrderId,
        );
      }
    } catch (err: any) {
      clearTimers();
      const errorDetail = err?.response?.data?.detail;
      const displayMsg =
        typeof errorDetail === "string"
          ? errorDetail
          : errorDetail?.message ||
            err?.message ||
            "Server issue initiating checkout. Please try again.";
      setCheckoutStatus("error");
      setCheckoutMessage(displayMsg);
      reportPaymentFailure(
        cleanEmail,
        "order_creation_error",
        displayMsg,
        activeOrderId,
      );
    }
  };

  // Cryptographic or Simulation Payment Verification
  const verifyPaymentSuccess = async (
    paymentData: {
      razorpay_order_id: string;
      razorpay_payment_id: string;
      razorpay_signature: string;
    },
    userEmail: string,
    plan: string,
  ) => {
    setCheckoutStatus("verifying");
    setCheckoutMessage(null);

    try {
      const { data } = await axios.post("/api/verify-payment", {
        razorpay_order_id: paymentData.razorpay_order_id,
        razorpay_payment_id: paymentData.razorpay_payment_id,
        razorpay_signature: paymentData.razorpay_signature,
        email: userEmail,
        plan: plan,
      });

      if (data.is_pro || data.status === "success") {
        // Unlock Pro in global client store & localStorage
        setUsage({
          used: usage?.used ?? 0,
          remaining: 999999,
          limit: 999999,
          is_pro: true,
        });

        try {
          localStorage.setItem("resumeroast_user_email", userEmail);
        } catch {}

        setCheckoutStatus("success");
        setCheckoutMessage(
          data.message ||
            "Payment verified successfully! Pro access is now active.",
        );
      } else {
        throw new Error(
          data.message || "Verification returned unexpected status.",
        );
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : err?.message || "Verification failed. Please contact support.";
      reportPaymentFailure(
        userEmail,
        "verification_failed",
        msg,
        paymentData.razorpay_order_id,
      );
      setCheckoutStatus("error");
      setCheckoutMessage(`Verification Error: ${msg}`);
    }
  };

  // Developer simulation helper for local test approval
  const handleSimulatePaymentApproval = async () => {
    if (!simulatedOrder) return;
    const simPaymentId = `pay_sim_${Date.now()}`;
    const simSignature = "sim_signature_dev_approved";

    await verifyPaymentSuccess(
      {
        razorpay_order_id: simulatedOrder.order_id,
        razorpay_payment_id: simPaymentId,
        razorpay_signature: simSignature,
      },
      email,
      simulatedOrder.plan,
    );
  };

  return (
    <main className="min-h-screen pb-24">
      {/* Top Bar */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-12">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link
            to="/"
            className="font-display text-lg tracking-tight text-paper select-none"
          >
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <div className="flex items-center gap-4">
            {returnUrl && returnUrl !== "/roast" && (
              <Link
                to={returnUrl}
                className="font-mono text-xs text-ember hover:underline"
              >
                ← Back to Roast
              </Link>
            )}
            <Link
              to="/"
              className="font-mono text-xs text-tan-dim hover:text-tan transition-colors"
            >
              Desk Home
            </Link>
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      <div className="max-w-[960px] mx-auto px-4">
        {/* Title */}
        <div className="text-center mb-12">
          <p className="section-label mb-3">
            HONEST PRICING // INDIA-FIRST CHECKOUT
          </p>
          <h1 className="font-display text-3xl sm:text-5xl text-paper tracking-tight mb-4">
            Free forever. Deep roast for Pro.
          </h1>
          <p className="font-mono text-xs text-tan-dim max-w-[540px] mx-auto leading-relaxed">
            Direct UPI, QR code, and Debit Cards. No mandatory recurring
            e-mandate surprises. Upgrade once and rewrite every single weak
            line.
          </p>

          {/* Toggle */}
          <div className="inline-flex items-center gap-4 mt-8 p-1 bg-white/[0.04] border border-white/[0.08] rounded-sm">
            <button
              type="button"
              onClick={() => setAnnual(false)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                !annual
                  ? "bg-bg text-paper border border-white/[0.08]"
                  : "text-tan-dim hover:text-tan"
              }`}
            >
              Monthly Pass
            </button>
            <button
              type="button"
              onClick={() => setAnnual(true)}
              className={`font-mono text-xs px-3 py-1.5 rounded-sm transition-colors ${
                annual
                  ? "bg-bg text-paper border border-white/[0.08]"
                  : "text-tan-dim hover:text-tan"
              }`}
            >
              Annual Pass{" "}
              <span className="text-ember font-bold">(-30% OFF)</span>
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
                <span className="font-mono text-xs text-tan-dim">
                  / forever
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Check top flaws quickly with zero account signup required. 1
                free roast every 24 hours.
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
              border: "2px solid #E8422D",
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
                  {annual ? "₹799" : "₹99"}
                </span>
                <span className="font-mono text-xs text-tan-dim">
                  {annual ? "/ year pass" : "/ month pass"}
                </span>
              </div>
              <p className="font-body text-xs text-tan mb-6 leading-relaxed">
                Full-line critique, all 5–8 flagged issues, instant bullet
                rewrites, high-res diploma, and unlimited daily submissions.
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

            {isLaunchingSoon ? (
              <button
                id="pro-launching-soon-button"
                type="button"
                onClick={() => {
                  setShowWaitlistModal(true);
                }}
                className="btn-primary w-full justify-center text-sm py-3 font-semibold shadow-lg hover:shadow-xl transition-all"
              >
                Pro launching soon 🔜
              </button>
            ) : (
              <button
                id="razorpay-initiate-button"
                type="button"
                onClick={() => {
                  setShowEmailModal(true);
                  setCheckoutStatus("idle");
                  setCheckoutMessage(null);
                }}
                className="btn-primary w-full justify-center text-sm py-3 font-semibold shadow-lg hover:shadow-xl transition-all"
              >
                {isTestMode
                  ? `Test Razorpay Checkout (${annual ? "₹799" : "₹99"})`
                  : `Unlock Pro Now (${annual ? "₹799" : "₹99"}) →`}
              </button>
            )}
          </div>
        </div>

        {/* Pro Launching Soon — VIP Waitlist Capture Section */}
        {isLaunchingSoon && (
          <div className="max-w-[800px] mx-auto mb-16 bg-[#16130F] border border-white/[0.12] rounded-sm p-6 sm:p-8 text-left shadow-xl animate-fadeIn">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="font-mono text-[10px] text-amber-400 font-bold bg-amber-400/10 border border-amber-400/30 px-2 py-0.5 rounded-sm uppercase tracking-wider">
                    VIP WAITLIST // EARLY ACCESS ⚡
                  </span>
                  <span className="font-mono text-[10px] text-tan-dim bg-white/[0.04] border border-white/[0.08] px-2 py-0.5 rounded-sm uppercase">
                    KYC Review in Progress
                  </span>
                </div>
                <h3 className="font-display text-xl sm:text-2xl text-paper">
                  Pro is almost here — we're finishing setup.
                </h3>
                <p className="font-mono text-xs text-tan-dim mt-1.5 max-w-xl leading-relaxed">
                  Want to know the moment Pro is live? Join the waitlist for
                  instant launch alert, 1 complimentary bonus roast, and an
                  exclusive early-adopter launch discount.
                </p>
              </div>
            </div>

            {inlineWaitlistStatus === "success" ||
            inlineWaitlistStatus === "already_joined" ? (
              <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-sm p-4 text-emerald-300 font-mono text-xs space-y-1 animate-fadeIn">
                <div className="font-bold flex items-center gap-2 text-emerald-200 text-sm">
                  <span>🎉</span>
                  <span>
                    {inlineWaitlistStatus === "success"
                      ? "You're on the VIP list!"
                      : "You're already on the list!"}
                  </span>
                </div>
                <p className="text-tan-dim">
                  {inlineWaitlistMessage ||
                    "We'll email you the second Pro is live 🎉"}
                </p>
                <p className="text-amber-300 text-[11px] pt-1 font-semibold">
                  🎁 Early-adopter launch discount + bonus roast locked in for
                  your email.
                </p>
              </div>
            ) : (
              <form onSubmit={handleInlineWaitlistSubmit} className="space-y-3">
                <div className="flex flex-col sm:flex-row items-stretch gap-3">
                  <input
                    type="email"
                    required
                    placeholder="Enter your email for instant launch alert"
                    value={inlineWaitlistEmail || email}
                    onChange={(e) => {
                      setInlineWaitlistEmail(e.target.value);
                      setEmail(e.target.value);
                    }}
                    disabled={inlineWaitlistLoading}
                    className="flex-1 bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-3 rounded-sm focus:outline-none focus:border-amber-400 disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={inlineWaitlistLoading}
                    className="btn-primary !py-3 !text-xs whitespace-nowrap font-medium"
                  >
                    {inlineWaitlistLoading
                      ? "Joining Waitlist…"
                      : "Get Launch Alert & Perk 🔜"}
                  </button>
                </div>
                {inlineWaitlistStatus === "error" && inlineWaitlistMessage && (
                  <p className="font-mono text-xs text-stamp">
                    ⚠ {inlineWaitlistMessage}
                  </p>
                )}
              </form>
            )}

            {/* Test Mode Entry point for developer / admin */}
            <div className="mt-6 pt-4 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-tan-dim">
              <span>Admin / gateway testing?</span>
              <button
                type="button"
                onClick={() => navigate("/pricing?test_checkout=true")}
                className="text-ember hover:underline"
              >
                Open Razorpay Test Mode Harness →
              </button>
            </div>
          </div>
        )}

        {/* Test Mode Harness & Diagnostics (Admin Only) */}
        {isTestMode && (
          <div className="max-w-[800px] mx-auto mb-16 bg-[#16130F] border border-amber-500/40 rounded-sm p-6 text-left shadow-lg animate-fadeIn">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-[10px] text-amber-400 font-bold bg-amber-400/10 border border-amber-400/30 px-2 py-0.5 rounded-sm uppercase">
                    🧪 Razorpay Test Mode Harness Active
                  </span>
                  {gatewayConfig?.mode === "test" && (
                    <span className="font-mono text-[10px] text-sky-400 bg-sky-400/10 border border-sky-400/30 px-2 py-0.5 rounded-sm uppercase">
                      Test Keys Configured
                    </span>
                  )}
                </div>
                <h3 className="font-display text-base sm:text-lg text-paper">
                  Admin / Developer Payment Test Environment
                </h3>
                <p className="font-mono text-xs text-tan-dim mt-1 max-w-xl leading-relaxed">
                  Public visitors see the "Pro Launching Soon" state and
                  waitlist capture. Use this view to validate the real Razorpay
                  checkout modal, UPI flow, and signature verification with test
                  credentials.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowManualUpi((v) => !v)}
                  className="btn-ghost !text-xs whitespace-nowrap shrink-0"
                >
                  {showManualUpi
                    ? "Hide UPI Details ▲"
                    : "View Test UPI Option ▼"}
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/pricing")}
                  className="btn-ghost !text-xs whitespace-nowrap shrink-0"
                >
                  Exit Test Mode ✕
                </button>
              </div>
            </div>

            {showManualUpi && (
              <div className="mt-5 pt-5 border-t border-white/[0.08] space-y-4 animate-fadeIn">
                <div className="bg-black/40 border border-white/[0.08] p-4 rounded-sm font-mono text-xs text-tan space-y-2">
                  <div>
                    <span className="text-tan-dim">UPI ID: </span>
                    <strong className="text-amber-300 font-bold select-all">
                      deveshsingh641@okaxis
                    </strong>
                  </div>
                  <div>
                    <span className="text-tan-dim">Amount: </span>
                    <span className="text-paper font-semibold">
                      {annual ? "₹799 (Annual Pass)" : "₹99 (Monthly Pass)"}
                    </span>
                  </div>
                  <div>
                    <span className="text-tan-dim">Scan or Pay: </span>
                    <span className="text-tan">
                      Send via GPay, PhonePe, Paytm, or BHIM, then paste the
                      12-digit UTR below.
                    </span>
                  </div>
                </div>

                {manualSubmitted ? (
                  <div className="p-3 bg-emerald-950/40 border border-emerald-500/50 rounded-sm font-mono text-xs text-emerald-300">
                    ✓ Payment reference recorded! Your Pro pass will be verified
                    and activated.
                  </div>
                ) : (
                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    <input
                      type="email"
                      placeholder="Your account email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="flex-1 bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-2.5 rounded-sm focus:outline-none focus:border-amber-400"
                    />
                    <input
                      type="text"
                      placeholder="12-digit UTR / Ref #"
                      value={manualUtr}
                      onChange={(e) => setManualUtr(e.target.value)}
                      className="flex-1 bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-2.5 rounded-sm focus:outline-none focus:border-amber-400"
                    />
                    <button
                      type="button"
                      disabled={manualLoading}
                      onClick={handleManualSubmit}
                      className="btn-primary !py-2.5 !text-xs whitespace-nowrap"
                    >
                      {manualLoading ? "Submitting…" : "Submit Reference"}
                    </button>
                  </div>
                )}

                {manualError && (
                  <p className="font-mono text-xs text-stamp">{manualError}</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Modal for Email & Razorpay In-Page Checkout */}
        {showEmailModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn">
            <div className="bg-[#14110E] border border-white/[0.12] rounded-sm p-6 sm:p-8 max-w-md w-full text-left space-y-4 relative shadow-2xl">
              <button
                type="button"
                onClick={() => {
                  setShowEmailModal(false);
                  setSimulatedOrder(null);
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
                Selected:{" "}
                <strong className="text-paper">
                  {annual ? "Pro Annual Pass (₹799)" : "Pro Monthly Pass (₹99)"}
                </strong>
                . Enter your email to open the in-page checkout modal.
              </p>

              {/* SUCCESS STATE */}
              {checkoutStatus === "success" ? (
                <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-sm p-5 space-y-3 animate-fadeIn">
                  <div className="flex items-center gap-2 text-emerald-300 font-display text-lg font-bold">
                    <span>🎉</span>
                    <span>Pro Subscription Activated!</span>
                  </div>
                  <p className="font-mono text-xs text-tan-dim leading-relaxed">
                    {checkoutMessage ||
                      "Your Pro pass is active. Unlimited submissions and all unlocked bullet rewrites are ready."}
                  </p>
                  <div className="pt-2 flex flex-col gap-2">
                    <button
                      type="button"
                      onClick={() => navigate(returnUrl)}
                      className="btn-primary w-full justify-center"
                    >
                      {returnUrl !== "/roast"
                        ? "Return to your Roast →"
                        : "Go to Resume Desk →"}
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
                    Running in test simulation mode. Test the full unlock flow
                    without actual payment:
                  </p>
                  <div className="bg-black/40 rounded-sm p-2.5 font-mono text-[11px] text-tan-dim space-y-1">
                    <div>
                      Order ID:{" "}
                      <span className="text-paper">
                        {simulatedOrder.order_id}
                      </span>
                    </div>
                    <div>
                      Amount:{" "}
                      <span className="text-paper">
                        ₹{simulatedOrder.amount / 100}
                      </span>{" "}
                      ({simulatedOrder.amount} paise)
                    </div>
                    <div>
                      User: <span className="text-paper">{email}</span>
                    </div>
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
                        setCheckoutStatus("failed");
                        setCheckoutMessage(
                          "Simulated bank decline: Insufficient balance or user declined.",
                        );
                        setSimulatedOrder(null);
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
                      disabled={
                        checkoutStatus === "creating_order" ||
                        checkoutStatus === "verifying"
                      }
                      className="w-full bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-3 rounded-sm focus:outline-none focus:border-stamp disabled:opacity-50"
                      autoFocus
                    />
                  </div>

                  {/* Explicit Error Alert (Part 1 requirement: No generic masks) */}
                  {checkoutMessage && (
                    <div
                      role="alert"
                      className={`p-3 rounded-sm text-left font-mono text-xs leading-relaxed border ${
                        checkoutStatus === "cancelled"
                          ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
                          : "bg-[#E8422D]/[0.1] border-[#E8422D]/40 text-[#ff8170]"
                      }`}
                    >
                      <div className="font-bold flex items-center gap-1.5 mb-0.5">
                        <span>
                          {checkoutStatus === "cancelled" ? "ℹ" : "⚠"}
                        </span>
                        <span>
                          {checkoutStatus === "cancelled"
                            ? "Notice"
                            : "Payment Notice"}
                        </span>
                      </div>
                      <p>{checkoutMessage}</p>
                    </div>
                  )}

                  <div className="flex gap-3 pt-2">
                    <button
                      id="razorpay-pay-button"
                      type="button"
                      disabled={
                        checkoutStatus === "creating_order" ||
                        checkoutStatus === "modal_open" ||
                        checkoutStatus === "verifying"
                      }
                      onClick={() => handleInitiatePayment(email)}
                      className="btn-primary flex-1 justify-center py-2.5 font-medium"
                    >
                      {checkoutStatus === "creating_order" ||
                      checkoutStatus === "modal_open" ? (
                        <span className="flex items-center gap-2">
                          <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          {loadingStage === "waiting"
                            ? "Checkout load hone mein thoda extra time lag raha hai. Please wait…"
                            : "Payment secure checkout khul raha hai…"}
                        </span>
                      ) : checkoutStatus === "verifying" ? (
                        <span className="flex items-center gap-2">
                          <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Verifying Access…
                        </span>
                      ) : checkoutStatus === "failed" ||
                        checkoutStatus === "cancelled" ||
                        checkoutStatus === "error" ? (
                        "Retry Payment"
                      ) : (
                        `Pay ${annual ? "₹799" : "₹99"} with UPI / Card`
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
          <div className="overflow-x-auto w-full max-w-full pb-2">
            <div className="gap-grid-1px grid-cols-3 min-w-[480px] sm:min-w-full border border-white/[0.08] rounded-sm overflow-hidden font-mono text-xs">
              {/* Header row */}
              <div className="p-4 text-tan-dim uppercase">Feature</div>
              <div className="p-4 text-tan-dim uppercase text-center">Free</div>
              <div className="p-4 text-stamp uppercase text-center font-semibold">
                Pro
              </div>

              {/* Comparison items */}
              {comparisonRows.map((row, idx) => (
                <React.Fragment key={`row-${idx}`}>
                  <div className="p-4 text-tan font-body text-xs">
                    {row.feature}
                  </div>
                  <div className="p-4 text-tan-dim text-center">{row.free}</div>
                  <div className="p-4 text-paper text-center font-medium">
                    {row.pro}
                  </div>
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* 7-Day Money-Back Guarantee & Support Banner */}
          <div className="mt-8 p-4 rounded-sm border border-emerald-500/20 bg-emerald-500/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-mono">
            <div className="flex items-center gap-2.5">
              <span className="text-emerald-400 text-base">🛡️</span>
              <div>
                <span className="text-paper font-semibold">
                  7-Day Money-Back Guarantee:
                </span>{" "}
                <span className="text-tan-dim">
                  Zero risk. If you encounter any technical fault or are
                  unsatisfied within 7 days, we issue a 100% refund.
                </span>
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0 text-[11px]">
              <Link
                to="/terms#refund-policy"
                className="text-amber-400 underline hover:text-amber-300"
              >
                Refund Policy
              </Link>
              <span className="text-white/20">·</span>
              <a
                href="mailto:support@resumeroast.app"
                className="text-tan hover:text-paper"
              >
                support@resumeroast.app
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Pro Launching Soon Waitlist Capture Modal */}
      <WaitlistModal
        isOpen={showWaitlistModal}
        onClose={() => setShowWaitlistModal(false)}
        source="pricing_pro_card"
      />
    </main>
  );
}
