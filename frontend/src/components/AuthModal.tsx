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

    try {
      const { data } = await axios.post("/api/auth/login", {
        email: cleanEmail,
      });

      if (data && data.ok) {
        setUserEmail(cleanEmail);

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
              ? `👑 Wah! Pro subscription active mil gaya for ${cleanEmail}! Aapka device sync ho chuka hai.`
              : `👑 Pro plan verified & active for ${cleanEmail}! Unlimited access is enabled.`,
          );
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
              ? `Signed in ho gaya as ${cleanEmail} (Free Tier). Agar aapne Pro khareeda hai toh wahi email daalein.`
              : `Signed in as ${cleanEmail} (Free Tier). If you purchased Pro, ensure this matches your checkout email.`,
          );
        }

        setTimeout(() => {
          if (onSuccess) onSuccess();
          onClose();
        }, 1400);
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : err?.message || "Failed to sign in. Please try again.";
      setErrorMsg(msg);
    } finally {
      setLoading(false);
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
              {isHinglish ? "Sign In / Sync Pro Plan" : "Sign In & Sync Pro Plan"}
            </h3>
            <p className="font-mono text-xs text-tan-dim mt-0.5">
              {isHinglish
                ? "Apna checkout email enter karein aur Pro plan sync karein."
                : "Enter your email to activate Pro and sync your plan across devices."}
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
              placeholder="e.g. yourname@gmail.com"
              className="w-full bg-black/60 border border-white/20 rounded-lg px-3.5 py-2.5 text-sm font-mono text-white placeholder:text-stone-600 focus:outline-none focus:border-amber-400 transition"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-stone-950 font-mono font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-amber-900/30 cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading
              ? isHinglish
                ? "Verifying..."
                : "Checking account..."
              : isHinglish
                ? "Sign In & Sync Pro ⚡"
                : "Sign In & Sync Pro ⚡"}
          </button>
        </form>

        <div className="mt-5 pt-4 border-t border-white/[0.08] text-center text-xs font-mono text-tan-dim">
          <span>
            {isHinglish
              ? "Agar Pro abhi nahi liya hai, toh aap standard Free tier me login honge."
              : "No password required. If you purchased Pro, it unlocks instantly on this device."}
          </span>
        </div>
      </div>
    </div>
  );
}
