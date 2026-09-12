import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import { useAppStore } from "@/store/useAppStore";
import { loadRazorpaySDK, RazorpaySuccessResponse } from "@/utils/razorpay";

type CheckoutStatus =
  | "idle"
  | "creating_order"
  | "modal_open"
  | "verifying"
  | "success"
  | "failed"
  | "cancelled"
  | "error";

interface SimulatedOrderData {
  order_id: string;
  amount: number;
  currency: string;
  plan: string;
  plan_name: string;
  message: string;
}

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultPlan?: "monthly" | "annual";
  returnUrl?: string;
  onSuccess?: () => void;
}

export default function CheckoutModal({
  isOpen,
  onClose,
  defaultPlan = "monthly",
  returnUrl = "/roast",
  onSuccess,
}: CheckoutModalProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const { usage, setUsage } = useAppStore();

  const [annual, setAnnual] = useState(defaultPlan === "annual");
  const [email, setEmail] = useState("");
  const [checkoutStatus, setCheckoutStatus] = useState<CheckoutStatus>("idle");
  const [checkoutMessage, setCheckoutMessage] = useState<string | null>(null);
  const [simulatedOrder, setSimulatedOrder] =
    useState<SimulatedOrderData | null>(null);
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

  // Sync defaultPlan when prop changes
  useEffect(() => {
    setAnnual(defaultPlan === "annual");
  }, [defaultPlan]);

  // Prepopulate email from localStorage
  useEffect(() => {
    if (isOpen) {
      try {
        const savedEmail = localStorage.getItem("resumeroast_user_email");
        if (savedEmail) {
          setEmail(savedEmail);
        }
      } catch {}
      setCheckoutStatus("idle");
      setCheckoutMessage(null);
      setSimulatedOrder(null);
      setLoadingStage("immediate");
    }
  }, [isOpen]);

  // Escape key closes modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        clearTimers();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleClose = () => {
    clearTimers();
    onClose();
  };

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

  const handleInitiatePayment = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@") || !cleanEmail.includes(".")) {
      setCheckoutStatus("error");
      setCheckoutMessage(
        isHinglish
          ? "Kripya valid email address daalein."
          : "Please enter a valid email address.",
      );
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
      `[Razorpay Checkout] 1. Initiating order creation for ${cleanEmail} (${annual ? "annual" : "monthly"}, retry=${isRetry})...`,
    );

    // Phase 2: After 3.2s, communicate that extra time is needed
    slowNoticeTimerRef.current = window.setTimeout(() => {
      setLoadingStage("waiting");
    }, 3200);

    // Phase 3: Client-side timeout guard ONLY while waiting for server order creation
    timeoutTimerRef.current = window.setTimeout(() => {
      setCheckoutStatus((current) => {
        if (current === "creating_order") {
          console.warn(
            "[Razorpay Checkout] Order creation timed out after 12s.",
          );
          setLoadingStage("timeout");
          const msg = isHinglish
            ? "Payment server se connect nahi ho paya. Kripya thodi der baad dubara koshish karein."
            : "Payment checkout could not connect. Please check your connection and try again.";
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
        `[Razorpay Checkout] 2. Server order created in ${(tOrder - tStart).toFixed(0)}ms:`,
        data.order_id,
      );

      // 3. Developer Simulation Mode (when keys not configured)
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
        const sdkErr = isHinglish
          ? "Razorpay checkout SDK load nahi hua. Ad-blocker ya internet connection check karein."
          : "Could not initialize Razorpay SDK. Please check your internet connection or ad-blocker.";
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
            console.info("[Razorpay Checkout] Modal dismissed by user.");
            setCheckoutStatus("cancelled");
            setCheckoutMessage(
              isHinglish
                ? "Payment window band ho gayi. Dubara koshish karne ke liye niche click karein."
                : "Payment window was dismissed. Click below to retry whenever you are ready.",
            );
          },
          confirm_close: true,
        },
        handler: async (response: RazorpaySuccessResponse) => {
          clearTimers();
          const tPaid = performance.now();
          console.info(
            `[Razorpay Checkout] Payment authorized in ${(tPaid - tStart).toFixed(0)}ms total. Verifying signature...`,
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
        console.warn("[Razorpay Checkout] Payment failed event:", failResp);
        setCheckoutStatus("failed");
        setCheckoutMessage(
          isHinglish
            ? `Payment Fail Ho Gaya: ${desc}. Koi amount deduct nahi hua.`
            : `Payment failed: ${desc}. No amount was deducted.`,
        );
        reportPaymentFailure(cleanEmail, "payment_failed", desc, activeOrderId);
      });

      // Crucial: Clear order-creation timers BEFORE opening Razorpay modal
      clearTimers();
      setCheckoutStatus("modal_open");
      const tOpen = performance.now();
      console.info(
        `[Razorpay Checkout] 3. Invoking rzp.open() at +${(tOpen - tStart).toFixed(0)}ms`,
      );

      try {
        rzp.open();
      } catch (openErr: any) {
        console.error("[Razorpay Checkout] rzp.open() threw error:", openErr);
        setCheckoutStatus("error");
        const openMsg = isHinglish
          ? "Payment popup block ho gaya. Kripya popup blocker disable karein aur dubara click karein."
          : "Payment popup was blocked or could not open. Please disable any popup blockers and try again.";
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
        setUsage({
          used: usage?.used ?? 0,
          remaining: 999999,
          limit: 999999,
          is_pro: true,
        });

        try {
          if (data.pro_token) {
            localStorage.setItem("resumeroast_pro_token", data.pro_token);
          }
          localStorage.setItem("resumeroast_is_pro", "true");
          localStorage.setItem("resumeroast_user_email", userEmail);
        } catch {}

        setCheckoutStatus("success");
        setCheckoutMessage(
          data.message ||
            (isHinglish
              ? "Payment successfully verify ho gaya! Pro access activate ho chuka hai."
              : "Payment verified successfully! Pro access is now active."),
        );
        if (onSuccess) {
          onSuccess();
        }
      } else {
        throw new Error(
          data.message || "Verification returned unexpected status.",
        );
      }
    } catch (err: any) {
      const errorDetail = err?.response?.data?.detail;
      const displayMsg =
        typeof errorDetail === "string"
          ? errorDetail
          : errorDetail?.message ||
            err?.message ||
            "Verification failed. Please contact support.";
      reportPaymentFailure(
        userEmail,
        "verification_failed",
        displayMsg,
        paymentData.razorpay_order_id,
      );
      setCheckoutStatus("error");
      setCheckoutMessage(`Verification Error: ${displayMsg}`);
    }
  };

  const handleSimulatePaymentApproval = async () => {
    if (!simulatedOrder) return;
    setCheckoutStatus("verifying");
    try {
      const { data } = await axios.post("/api/verify-payment", {
        razorpay_order_id: simulatedOrder.order_id,
        razorpay_payment_id: `pay_sim_${Date.now()}`,
        razorpay_signature: "simulated_signature_bypass",
        email: email.trim().toLowerCase(),
        plan: simulatedOrder.plan,
      });

      setUsage({
        used: usage?.used ?? 0,
        remaining: 999999,
        limit: 999999,
        is_pro: true,
      });

      try {
        if (data.pro_token) {
          localStorage.setItem("resumeroast_pro_token", data.pro_token);
        }
        localStorage.setItem("resumeroast_is_pro", "true");
        localStorage.setItem(
          "resumeroast_user_email",
          email.trim().toLowerCase(),
        );
      } catch {}

      setCheckoutStatus("success");
      setCheckoutMessage(
        data.message || "Simulation mode payment approved. Pro unlocked!",
      );
      setSimulatedOrder(null);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err: any) {
      setCheckoutStatus("error");
      setCheckoutMessage("Simulation verification failed.");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn"
      onClick={handleClose}
    >
      <div
        className="relative w-full max-w-md bg-[#16130F] border border-stamp/40 rounded-sm p-6 sm:p-7 text-left shadow-2xl space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-4 right-4 text-tan-dim hover:text-tan font-mono text-sm"
          aria-label="Close"
        >
          ✕
        </button>

        {/* Header Badges */}
        <div className="flex items-center gap-2">
          <span className="section-label">
            {isHinglish ? "INSTANT PRO UNLOCK" : "INSTANT CHECKOUT"}
          </span>
          <span className="font-mono text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-500/30 px-1.5 py-0.5 rounded-sm">
            ⚡ UPI, Cards & Netbanking
          </span>
        </div>

        <h2 className="font-display text-2xl text-paper">
          {isHinglish ? "Resume Roast Pro Unlock Karo" : "Unlock Pro Access"}
        </h2>

        {/* Plan Selector Toggle */}
        <div className="flex items-center gap-2 p-1 bg-black/40 border border-white/[0.08] rounded-sm text-xs font-mono">
          <button
            type="button"
            onClick={() => setAnnual(false)}
            className={`flex-1 py-1.5 px-2 rounded-sm text-center transition-all ${
              !annual
                ? "bg-stamp text-paper font-semibold shadow"
                : "text-tan-dim hover:text-tan"
            }`}
          >
            {isHinglish ? "Monthly (₹99)" : "Monthly (₹99)"}
          </button>
          <button
            type="button"
            onClick={() => setAnnual(true)}
            className={`flex-1 py-1.5 px-2 rounded-sm text-center transition-all ${
              annual
                ? "bg-stamp text-paper font-semibold shadow"
                : "text-tan-dim hover:text-tan"
            }`}
          >
            {isHinglish
              ? "Annual (₹799 · 33% Off)"
              : "Annual (₹799 · Save 33%)"}
          </button>
        </div>

        <p className="font-body text-xs text-tan leading-relaxed">
          {isHinglish
            ? "Unlimited daily roasts, saare 5-8 issues, aur concrete rewritten bullet points."
            : "Unlimited daily roasts, all 5-8 flagged issues, and full bullet rewrites."}
        </p>

        {/* SUCCESS STATE */}
        {checkoutStatus === "success" ? (
          <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-sm p-5 space-y-3 animate-fadeIn">
            <div className="flex items-center gap-2 text-emerald-300 font-display text-lg font-bold">
              <span>🎉</span>
              <span>
                {isHinglish ? "Payment ho gaya 🎉" : "Payment Successful 🎉"}
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              {checkoutMessage ||
                (isHinglish
                  ? "Pro unlock ho gaya. Ab full power mein resume roast karo."
                  : "Pro access is active. Unlimited submissions & bullet rewrites unlocked.")}
            </p>
            <div className="pt-2 flex flex-col gap-2">
              <button
                type="button"
                onClick={onClose}
                className="btn-primary w-full justify-center"
              >
                {isHinglish ? "Roast Karna Shuru Karo →" : "Start Roasting →"}
              </button>
            </div>
          </div>
        ) : simulatedOrder ? (
          /* DEVELOPER SIMULATION MODAL */
          <div className="bg-amber-950/30 border border-amber-500/40 rounded-sm p-4 space-y-3 animate-fadeIn">
            <div className="flex items-center gap-2 text-amber-300 font-mono text-xs font-bold uppercase">
              <span>🛠️</span>
              <span>Developer Simulation Mode</span>
            </div>
            <p className="font-mono text-xs text-tan leading-relaxed">
              Simulated order generated. Click below to test instant approval:
            </p>
            <div className="bg-black/40 rounded-sm p-2.5 font-mono text-[11px] text-tan-dim space-y-1">
              <div>
                Order ID:{" "}
                <span className="text-paper">{simulatedOrder.order_id}</span>
              </div>
              <div>
                Amount:{" "}
                <span className="text-paper">
                  ₹{simulatedOrder.amount / 100}
                </span>
              </div>
            </div>
            <button
              type="button"
              onClick={handleSimulatePaymentApproval}
              className="btn-primary w-full justify-center text-xs py-2.5 font-semibold"
            >
              ✓ Simulate Success (Unlock Pro)
            </button>
          </div>
        ) : (
          /* STANDARD FORM */
          <form onSubmit={handleInitiatePayment} className="space-y-4">
            <div>
              <label
                htmlFor="checkout-email-input"
                className="block font-mono text-[11px] text-tan-dim mb-1 uppercase tracking-wider"
              >
                {isHinglish
                  ? "Receipt & Pro Access ke liye Email:"
                  : "Email address for your receipt & access:"}
              </label>
              <input
                id="checkout-email-input"
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
                required
              />
            </div>

            {/* Error / Status Message */}
            {checkoutMessage && (
              <div
                role="alert"
                className={`p-3 rounded-sm text-left font-mono text-xs leading-relaxed border ${
                  checkoutStatus === "cancelled"
                    ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
                    : "bg-[#E8422D]/[0.1] border-[#E8422D]/40 text-[#ff8170]"
                }`}
              >
                {checkoutStatus === "cancelled" ? "ℹ" : "⚠"} {checkoutMessage}
              </div>
            )}

            {/* Submit / Pay Button */}
            <button
              id="checkout-modal-pay-button"
              type="submit"
              disabled={
                checkoutStatus === "creating_order" ||
                checkoutStatus === "modal_open" ||
                checkoutStatus === "verifying"
              }
              className="btn-primary w-full justify-center text-sm py-3.5 font-semibold shadow-lg hover:shadow-xl transition-all disabled:opacity-50"
            >
              {checkoutStatus === "creating_order" ||
              checkoutStatus === "modal_open" ? (
                <span className="flex items-center gap-2 font-mono text-xs">
                  <span className="animate-spin inline-block">⚡</span>
                  {loadingStage === "waiting"
                    ? isHinglish
                      ? "Checkout load hone mein thoda extra time lag raha hai. Please wait…"
                      : "Checkout is taking extra time to load. Please wait…"
                    : isHinglish
                      ? "Payment secure checkout khul raha hai…"
                      : "Opening secure payment checkout…"}
                </span>
              ) : checkoutStatus === "verifying" ? (
                <span className="flex items-center gap-2 font-mono text-xs">
                  <span className="animate-spin inline-block">🔒</span>
                  Verifying Payment Signature…
                </span>
              ) : isHinglish ? (
                `Pay with Razorpay (${annual ? "₹799" : "₹99"}) →`
              ) : (
                `Pay with Razorpay (${annual ? "₹799" : "₹99"}) →`
              )}
            </button>

            {/* Payment security info */}
            <div className="flex items-center justify-center gap-4 text-[10px] font-mono text-tan-dim/80 pt-1">
              <span>🔒 256-Bit SSL Encrypted</span>
              <span>⚡ Official Razorpay SDK</span>
              <span>🇮🇳 Made in India</span>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
