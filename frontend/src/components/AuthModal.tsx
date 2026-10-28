import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import { useAppStore } from "@/store/useAppStore";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

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
  const [isWakingUp, setIsWakingUp] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isProDetected, setIsProDetected] = useState<boolean | null>(null);

  const [elapsedSecs, setElapsedSecs] = useState(0);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wakeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastCheckedEmailRef = useRef<string>("");

  // Sync / Login execution function
  const performSync = async (cleanEmail: string, explicitPaymentId?: string) => {
    if (!cleanEmail || !EMAIL_REGEX.test(cleanEmail)) return;

    setLoading(true);
    setIsWakingUp(false);
    setElapsedSecs(0);
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsProDetected(null);

    if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    elapsedTimerRef.current = setInterval(() => {
      setElapsedSecs((s) => s + 1);
    }, 1000);

    // If server takes > 2.5s (e.g. Render cold start), show helpful status
    if (wakeTimerRef.current) clearTimeout(wakeTimerRef.current);
    wakeTimerRef.current = setTimeout(() => {
      setIsWakingUp(true);
    }, 2500);

    const payload: Record<string, any> = { email: cleanEmail };
    const pid = (explicitPaymentId !== undefined ? explicitPaymentId : paymentId).trim();
    if (pid) {
      payload.payment_id = pid;
    }

    let data: any = null;
    let lastError: any = null;

    // Primary endpoint: /api/auth/login (timeout: 45 seconds for cold start)
    try {
      const res = await axios.post("/api/auth/login", payload, { timeout: 45000 });
      if (res && res.data && (res.data.ok || res.data.is_pro !== undefined)) {
        data = res.data;
      }
    } catch (err: any) {
      lastError = err;
      // On 404, fallback to /api/payment/reconcile
      if (err?.response?.status === 404) {
        try {
          const res = await axios.post("/api/payment/reconcile", payload, { timeout: 45000 });
          if (res && res.data && (res.data.ok || res.data.is_pro !== undefined || res.data.status)) {
            data = res.data;
          }
        } catch (fbErr: any) {
          lastError = fbErr;
        }
      }
    } finally {
      if (wakeTimerRef.current) clearTimeout(wakeTimerRef.current);
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
      setLoading(false);
      setIsWakingUp(false);
    }

    if (data && (data.ok || data.is_pro !== undefined)) {
      lastCheckedEmailRef.current = cleanEmail;
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
        }, 1200);
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
      const code = lastError?.code;
      const status = lastError?.response?.status;
      let msg = "Failed to sign in. Please try again.";

      if (code === "ECONNABORTED" || lastError?.message?.includes("timeout")) {
        msg = isHinglish
          ? "Server respond karne mein time le raha hai (waking up). Kripya 'Retry' karein."
          : "Server connection timed out while waking up. Please click Retry.";
      } else if (status === 404) {
        msg = isHinglish
          ? "Server deployment in progress hai. Kripya 10 second baad retry karein ya Payment ID daalein."
          : "Server is updating. Please retry in 10-15 seconds, or enter your Payment ID below.";
      } else {
        const detail = lastError?.response?.data?.detail;
        msg = typeof detail === "string" ? detail : (lastError?.message || msg);
      }

      setErrorMsg(msg);
      setShowPaymentIdInput(true);
    }
  };

  // Automatic Sync: as soon as user types or pastes a valid email address
  useEffect(() => {
    if (!isOpen) return;
    const cleanEmail = email.trim().toLowerCase();

    if (EMAIL_REGEX.test(cleanEmail) && cleanEmail !== lastCheckedEmailRef.current && !loading) {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        performSync(cleanEmail);
      }, 500);
    }

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [email, isOpen]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      if (wakeTimerRef.current) clearTimeout(wakeTimerRef.current);
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    };
  }, []);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
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
    performSync(cleanEmail);
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
                ? "Email daalein. Free tier ho ya Pro, automatically sync ho jayega."
                : "Enter your email to sign in or instantly sync your Pro plan across devices."}
            </p>
          </div>
        </div>

        {/* Live waking-up indicator */}
        {isWakingUp && (
          <div className="mb-4 p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 font-mono text-xs flex items-center gap-2 animate-pulse">
            <span className="inline-block animate-spin">⏳</span>
            <span>
              {isHinglish
                ? `Server wake ho raha hai (${elapsedSecs}s)... Render free tier cold-start le raha hai, kripya thoda wait karein.`
                : `Waking up secure server (${elapsedSecs}s)... Cold start in progress, please hold on.`}
            </span>
          </div>
        )}

        {/* Error message with prominent Retry */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-xs leading-relaxed flex flex-col gap-2.5">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span>⚠️ </span>
                <span>{errorMsg}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={() => performSync(email.trim().toLowerCase())}
              className="w-full py-2 px-3 rounded bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold text-xs uppercase tracking-wider transition cursor-pointer flex items-center justify-center gap-1.5 shadow-sm shadow-amber-900/40"
            >
              <span>⚡</span>
              <span>
                {isHinglish
                  ? "Server Ab Wake Ho Chuka Hai — Click to Retry"
                  : "Server is now awake — Click to Retry"}
              </span>
            </button>
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
            <div className="flex items-center justify-between mb-1.5">
              <label className="block font-mono text-[11px] uppercase tracking-wider text-tan-dim font-bold">
                {isHinglish ? "Email Address" : "Email Address"}
              </label>
              {loading && (
                <span className="font-mono text-[11px] text-amber-400 flex items-center gap-1">
                  <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-ping" />
                  Auto-syncing...
                </span>
              )}
            </div>
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
                  ? "Agar email se match na ho toh Razorpay confirmation SMS se Payment ID daalein."
                  : "Found in your Razorpay confirmation SMS/email receipt."}
              </p>
            </div>
          ) : (
            <div className="text-right">
              <button
                type="button"
                onClick={() => setShowPaymentIdInput(true)}
                className="text-[11px] font-mono text-tan-dim hover:text-amber-400 underline underline-offset-2 transition cursor-pointer"
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
            className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-stone-950 font-mono font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-amber-900/30 cursor-pointer disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="inline-block w-3.5 h-3.5 border-2 border-stone-950 border-t-transparent rounded-full animate-spin" />
                <span>
                  {isWakingUp
                    ? isHinglish
                      ? "Server Waking Up..."
                      : "Server Waking Up..."
                    : isHinglish
                      ? "Syncing Account..."
                      : "Syncing Account..."}
                </span>
              </>
            ) : (
              <span>
                {isHinglish
                  ? "Continue / Sync Email →"
                  : "Continue / Sync Email →"}
              </span>
            )}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-white/[0.08] text-center text-xs font-mono text-tan-dim leading-relaxed">
          <span>
            {isHinglish
              ? "Password ki zaroorat nahi hai. Email enter karte hi automatic sync ho jayega."
              : "Zero password needed. Entering your email automatically synchronizes your account."}
          </span>
        </div>
      </div>
    </div>
  );
}
