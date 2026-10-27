import React, { useState } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import { useAppStore } from "@/store/useAppStore";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function AuthModal({
  isOpen,
  onClose,
  onSuccess,
}: AuthModalProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const { setUsage, setUserEmail } = useAppStore();

  const [email, setEmail] = useState(() => {
    return (
      (typeof window !== "undefined" &&
        localStorage.getItem("resumeroast_user_email")) ||
      ""
    );
  });
  const [paymentId, setPaymentId] = useState("");
  const [showPaymentIdInput, setShowPaymentIdInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isProDetected, setIsProDetected] = useState<boolean | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setErrorMsg(
        isHinglish
          ? "Kripya sahi email address enter karein (e.g. name@gmail.com)."
          : "Please enter a valid email address.",
      );
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsProDetected(null);

    const cleanPaymentId = paymentId.trim();
    const endpoints = [
      "/api/auth/login",
      "/api/payment/reconcile",
      "/api/reconcile",
      "/api/billing/reconcile",
      "/api/payment/login",
    ];

    let data: any = null;
    let lastError: any = null;

    for (const endpoint of endpoints) {
      try {
        const payload: Record<string, any> = { email: cleanEmail };
        if (cleanPaymentId) {
          payload.payment_id = cleanPaymentId;
        }

        const res = await axios.post(endpoint, payload);
        if (res && res.data && (res.data.ok || res.data.is_pro !== undefined || res.data.status)) {
          data = res.data;
          break;
        }
      } catch (err: any) {
        lastError = err;
        // If server responded with a non-404 error (e.g. 422 validation), don't blindly loop
        if (err?.response?.status && err.response.status !== 404) {
          break;
        }
      }
    }

    setLoading(false);

    if (data && (data.ok || data.is_pro !== undefined)) {
      setUserEmail(cleanEmail);
      if (typeof window !== "undefined") {
        localStorage.setItem("resumeroast_user_email", cleanEmail);
      }

      if (data.token) {
        localStorage.setItem("resumeroast_pro_token", data.token);
        sessionStorage.setItem("resumeroast_pro_token", data.token);
      }

      if (data.is_pro) {
        setIsProDetected(true);
        setUsage({
          used: 0,
          remaining: 999999,
          limit: 999999,
          is_pro: true,
        });
        setSuccessMsg(
          isHinglish
            ? `👑 Wah! Pro subscription active mil gaya for ${cleanEmail}! Unlimited roasts unlock ho gaye.`
            : `👑 Pro plan verified & active for ${cleanEmail}! Unlimited access is enabled.`,
        );

        setTimeout(() => {
          if (onSuccess) onSuccess();
          onClose();
        }, 1500);
      } else {
        setIsProDetected(false);
        setUsage({
          used: 0,
          remaining: 1,
          limit: 1,
          is_pro: false,
        });
        setSuccessMsg(
          isHinglish
            ? `Signed in as ${cleanEmail} (Free Tier). Agar aapne Pro khareeda hai toh Payment ID enter karein.`
            : `Signed in as ${cleanEmail} (Free Tier). If you purchased Pro, enter your Razorpay Payment ID below.`,
        );
        setShowPaymentIdInput(true);
      }
    } else {
      const status = lastError?.response?.status;
      let msg = "Failed to sign in. Please try again.";
      if (status === 404) {
        msg = isHinglish
          ? "Server update in progress hai ya wake ho rha hai. Kripya 10 second baad retry karein ya Payment ID daalein."
          : "Server is updating or restarting. Please retry in 10-15 seconds, or enter your Razorpay Payment ID.";
      } else {
        const detail = lastError?.response?.data?.detail;
        msg =
          typeof detail === "string"
            ? detail
            : lastError?.message || msg;
      }
      setErrorMsg(msg);
      setShowPaymentIdInput(true);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fadeIn"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md bg-[#161311] border border-white/15 rounded-xl p-6 sm:p-7 shadow-2xl relative text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-stone-400 hover:text-white text-lg p-1 transition"
          aria-label="Close modal"
        >
          ✕
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-xl shrink-0">
            👤
          </div>
          <div>
            <h3 className="font-display text-lg font-bold text-white tracking-tight">
              {isHinglish ? "Account Sign In" : "Account Sign In"}
            </h3>
            <p className="font-mono text-xs text-tan-dim mt-0.5">
              {isHinglish
                ? "Email daalein. Free tier ho ya Pro, aapka account yahan se sync ho jayega."
                : "Enter your email to sign in or instantly sync your Pro plan across devices."}
            </p>
          </div>
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs leading-relaxed">
            ⚠️ {errorMsg}
          </div>
        )}

        {/* Success message */}
        {successMsg && (
          <div
            className={`mb-4 p-3 rounded font-mono text-xs leading-relaxed border ${
              isProDetected
                ? "bg-amber-500/15 border-amber-500/40 text-amber-300"
                : "bg-emerald-500/15 border-emerald-500/30 text-emerald-300"
            }`}
          >
            {successMsg}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-tan-dim font-bold mb-1.5">
              {isHinglish ? "Email Address" : "Email Address"}
            </label>
            <input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. ankitprjsoft@gmail.com"
              className="w-full bg-black/60 border border-white/20 rounded-lg px-3.5 py-2.5 text-sm font-mono text-white placeholder:text-stone-600 focus:outline-none focus:border-amber-400 transition"
            />
          </div>

          {/* Optional Razorpay Payment ID toggle */}
          {showPaymentIdInput ? (
            <div className="animate-fadeIn">
              <label className="block font-mono text-[11px] uppercase tracking-wider text-amber-400 font-bold mb-1.5">
                {isHinglish
                  ? "Razorpay Payment ID (Optional)"
                  : "Razorpay Payment ID (Optional)"}
              </label>
              <input
                type="text"
                value={paymentId}
                onChange={(e) => setPaymentId(e.target.value)}
                placeholder="e.g. pay_TsoYydo0zY4KrB"
                className="w-full bg-black/60 border border-amber-500/30 rounded-lg px-3.5 py-2 text-xs font-mono text-amber-200 placeholder:text-stone-600 focus:outline-none focus:border-amber-400 transition"
              />
              <p className="font-mono text-[10px] text-tan-dim mt-1">
                {isHinglish
                  ? "Agar email se match na ho toh SMS/email se Razorpay payment ID copy karke paste karein."
                  : "Found in your Razorpay confirmation SMS/email receipt."}
              </p>
            </div>
          ) : (
            <div className="text-right">
              <button
                type="button"
                onClick={() => setShowPaymentIdInput(true)}
                className="text-[11px] font-mono text-tan-dim hover:text-amber-400 underline underline-offset-2 transition"
              >
                {isHinglish
                  ? "+ Have a Razorpay Payment ID?"
                  : "+ Have a Razorpay Payment ID?"}
              </button>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-stone-950 font-mono font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-amber-900/30 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading
              ? isHinglish
                ? "Connecting..."
                : "Connecting..."
              : isHinglish
                ? "Continue with Email →"
                : "Continue with Email →"}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-white/[0.08] text-center text-xs font-mono text-tan-dim leading-relaxed">
          <span>
            {isHinglish
              ? "Password ki zaroorat nahi hai. Agar Pro liya hua hai toh unlimited roasts instantly unlock ho jayenge."
              : "Zero password needed. Free accounts get 1 daily roast, and Pro accounts unlock unlimited access automatically."}
          </span>
        </div>
      </div>
    </div>
  );
}
