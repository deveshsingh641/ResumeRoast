import React, { useState, useEffect } from "react";
import axios from "axios";

interface WaitlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  source?: string;
  headline?: string;
  subheadline?: string;
}

export default function WaitlistModal({
  isOpen,
  onClose,
  source = "generic_pro_cta",
  headline = "Pro is Launching Soon 🔜",
  subheadline = "We're finishing the last payment gateway checks. Drop your email to get instant access the second Pro goes live, plus an early-bird launch perk.",
}: WaitlistModalProps) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<
    "idle" | "success" | "already_joined" | "error"
  >("idle");
  const [message, setMessage] = useState<string | null>(null);

  // Pre-fill email from localStorage if user previously entered it
  useEffect(() => {
    if (isOpen) {
      try {
        const savedEmail = localStorage.getItem("resumeroast_user_email");
        if (savedEmail && !email) {
          setEmail(savedEmail);
        }
      } catch {}
      setStatus("idle");
      setMessage(null);
    }
  }, [isOpen]);

  // ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanEmail = email.trim().toLowerCase();

    if (!cleanEmail || !cleanEmail.includes("@") || !cleanEmail.includes(".")) {
      setStatus("error");
      setMessage("Please enter a valid email address.");
      return;
    }

    try {
      setLoading(true);
      setStatus("idle");
      setMessage(null);

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
        source: source,
        user_id: userId,
      });

      if (data.is_already_on_list || data.status === "already_joined") {
        setStatus("already_joined");
        setMessage(
          data.message ||
            "You're already on the list! We'll email you the second Pro is live 🎉",
        );
      } else {
        setStatus("success");
        setMessage(
          data.message ||
            "You're on the list — we'll email you the second Pro is live 🎉",
        );
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : err?.message || "Could not join waitlist. Please try again.";
      setStatus("error");
      setMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="waitlist-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-[#14110E] border border-white/[0.14] rounded-sm p-6 sm:p-8 max-w-md w-full text-left space-y-5 relative shadow-2xl">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close modal"
          className="absolute top-4 right-4 text-tan-dim hover:text-paper font-mono text-sm transition-colors p-1"
        >
          ✕
        </button>

        {/* Header Tag */}
        <div className="flex items-center gap-2">
          <span className="section-label">EARLY ACCESS QUEUE</span>
          <span className="font-mono text-[10px] text-amber-400 bg-amber-950/60 border border-amber-500/30 px-2 py-0.5 rounded-sm">
            Launch Day Perks ⚡
          </span>
        </div>

        {/* Title */}
        <div>
          <h2
            id="waitlist-title"
            className="font-display text-2xl text-paper tracking-tight"
          >
            {headline}
          </h2>
          <p className="font-body text-xs text-tan mt-2 leading-relaxed">
            {subheadline}
          </p>
        </div>

        {/* Success / Already Joined Banner */}
        {status === "success" || status === "already_joined" ? (
          <div className="bg-emerald-950/40 border border-emerald-500/50 rounded-sm p-5 space-y-3 animate-fadeIn">
            <div className="flex items-center gap-2 text-emerald-300 font-display text-lg font-bold">
              <span>{status === "success" ? "🎉" : "✓"}</span>
              <span>
                {status === "success"
                  ? "You’re on the VIP Waitlist!"
                  : "Already Reserved!"}
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              {message}
            </p>
            <div className="pt-2 border-t border-white/[0.08] space-y-1 text-tan font-mono text-[11px]">
              <p className="text-amber-400 font-semibold">
                🎁 Early-adopter perk locked in:
              </p>
              <p className="text-tan-dim">
                Launch discount + 1 extra complimentary deep roast credited to
                your email.
              </p>
            </div>
            <div className="pt-3">
              <button
                type="button"
                onClick={onClose}
                className="btn-primary w-full justify-center text-xs py-2.5 font-medium"
              >
                Done / Back to Roast →
              </button>
            </div>
          </div>
        ) : (
          /* Input & Capture Form */
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="waitlist-email-input"
                className="block font-mono text-[11px] text-tan-dim mb-1 uppercase tracking-wider"
              >
                Where should we notify you?
              </label>
              <input
                id="waitlist-email-input"
                type="email"
                required
                placeholder="name@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                className="w-full bg-[#1A1612] border border-white/[0.15] text-paper font-mono text-xs p-3 rounded-sm focus:outline-none focus:border-stamp disabled:opacity-50"
                autoFocus
              />
            </div>

            {/* Error banner */}
            {status === "error" && message && (
              <div
                role="alert"
                className="p-3 bg-[#E8422D]/[0.1] border border-[#E8422D]/40 text-[#ff8170] rounded-sm text-left font-mono text-xs leading-relaxed"
              >
                ⚠ {message}
              </div>
            )}

            {/* Early bird perk highlight */}
            <div className="p-3 bg-white/[0.03] border border-white/[0.06] rounded-sm font-mono text-[11px] text-tan-dim leading-relaxed">
              <span className="text-amber-300 font-semibold">
                ⚡ Early Bird Bonus:
              </span>{" "}
              Waitlist signups receive a special launch discount + first queue
              priority the instant payments open.
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-1">
              <button
                type="submit"
                disabled={loading}
                className="btn-primary flex-1 justify-center py-2.5 font-medium text-xs whitespace-nowrap"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Adding…
                  </span>
                ) : (
                  "Notify Me at Launch 🔜"
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="btn-ghost text-xs py-2.5"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
