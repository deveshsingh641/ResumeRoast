import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";

export interface BulletRewriteOption {
  style: string;
  badge: string;
  rewritten_text: string;
  explanation: string;
}

interface BulletRewriterModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialBullet?: string;
  initialRole?: string;
}

export default function BulletRewriterModal({
  isOpen,
  onClose,
  initialBullet = "",
  initialRole = "",
}: BulletRewriterModalProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";

  const [bullet, setBullet] = useState(initialBullet);
  const [role, setRole] = useState(initialRole);
  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState<BulletRewriteOption[]>([]);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Sync initial bullet when opened
  useEffect(() => {
    if (isOpen) {
      setBullet(initialBullet);
      setRole(initialRole);
      setError(null);
      // If we opened with a non-empty initial bullet, auto-generate rewrites
      if (initialBullet.trim().length >= 10 && options.length === 0) {
        handleRewrite(initialBullet, initialRole);
      }
    }
  }, [isOpen, initialBullet, initialRole]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleRewrite = async (bulletText: string, targetRole: string) => {
    const textToSubmit = bulletText.trim();
    if (!textToSubmit) {
      setError(
        isHinglish
          ? "Bullet point khali mat chhod yaar."
          : "Please enter a bullet point to rewrite.",
      );
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const { data } = await axios.post("/api/rewrite-bullet", {
        bullet: textToSubmit,
        target_role: targetRole.trim() || undefined,
        language: normalizeLang(i18n.language),
      });

      if (data?.ok && Array.isArray(data?.data?.options)) {
        setOptions(data.data.options);
      } else {
        setError(
          isHinglish
            ? "Rewrites generate nahi ho paye, try again."
            : "Could not generate rewrites. Please try again.",
        );
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to generate rewrites.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, idx: number) => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md animate-fadeIn"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col bg-[#12110D] border border-white/20 rounded-xl shadow-2xl overflow-hidden animate-slideUp">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10 bg-[#1A1814]/80">
          <div className="flex items-center gap-2.5">
            <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-ember/20 text-ember border border-ember/30 text-base">
              ⚡
            </span>
            <div>
              <h2 className="font-mono text-sm sm:text-base font-bold text-paper flex items-center gap-2">
                {isHinglish
                  ? "AI Bullet Improver (STAR Method)"
                  : "AI Bullet Point Improver"}
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-ember/20 text-ember border border-ember/40">
                  STAR Formula
                </span>
              </h2>
              <p className="font-mono text-[11px] text-tan-dim">
                {isHinglish
                  ? "Vague lines ko metrics aur action verbs ke saath convert karo."
                  : "Turn passive job duties into high-impact, quantified recruiter magnets."}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-tan-dim hover:text-white hover:bg-white/10 transition-colors focus:outline-none"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Input Area */}
          <div>
            <label className="block font-mono text-[11px] uppercase tracking-wider text-tan-dim mb-1.5">
              {isHinglish
                ? "Apna Weak Bullet Point Yahan Daalo:"
                : "Original Bullet Point:"}
            </label>
            <textarea
              rows={2}
              value={bullet}
              onChange={(e) => setBullet(e.target.value)}
              placeholder={
                isHinglish
                  ? "e.g. Worked on frontend bugs and assisted team in weekly release."
                  : "e.g. Responsible for developing microservices and helping team members."
              }
              className="w-full bg-black/50 border border-white/15 rounded-lg p-3 text-xs sm:text-sm font-mono text-paper placeholder:text-stone-600 focus:outline-none focus:border-ember transition"
            />
          </div>

          {/* Optional Role Input & Submit Button Row */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            <div className="flex-1">
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder={
                  isHinglish
                    ? "Target Role (optional, e.g. Frontend Engineer)"
                    : "Target Role (optional, e.g. Backend SDE)"
                }
                className="w-full bg-black/50 border border-white/15 rounded-lg px-3 py-2 text-xs font-mono text-paper placeholder:text-stone-600 focus:outline-none focus:border-ember transition"
              />
            </div>
            <button
              onClick={() => handleRewrite(bullet, role)}
              disabled={loading || !bullet.trim()}
              className="btn-primary !py-2 !px-4 text-xs font-mono flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <span className="w-3.5 h-3.5 border-2 border-bg border-t-transparent rounded-full animate-spin" />
                  <span>{isHinglish ? "Generating..." : "Rewriting..."}</span>
                </>
              ) : (
                <>
                  <span>⚡</span>
                  <span>
                    {isHinglish
                      ? "STAR Rewrites Generate Karo"
                      : "Generate 3 STAR Rewrites"}
                  </span>
                </>
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 rounded-lg bg-stamp/15 border border-stamp/30 font-mono text-xs text-stamp animate-fadeIn">
              ⚠️ {error}
            </div>
          )}

          {/* Generated Results */}
          {options.length > 0 && (
            <div className="pt-2 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs uppercase tracking-wider text-tan font-bold">
                  {isHinglish
                    ? "3 High-Converting Variations:"
                    : "3 High-Converting Variations:"}
                </span>
                <span className="font-mono text-[11px] text-tan-dim">
                  {isHinglish
                    ? "1-click copy karke resume mein paste karo"
                    : "Click to copy directly into your resume"}
                </span>
              </div>

              {options.map((opt, idx) => {
                const isCopied = copiedIdx === idx;
                const badgeColor =
                  idx === 0
                    ? "text-ember bg-ember/15 border-ember/30"
                    : idx === 1
                      ? "text-cyan-400 bg-cyan-400/15 border-cyan-400/30"
                      : "text-emerald-400 bg-emerald-400/15 border-emerald-400/30";

                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-lg bg-[#181612] border border-white/10 hover:border-white/20 transition-all group"
                  >
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className={`font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${badgeColor}`}
                        >
                          {opt.badge}
                        </span>
                        <span className="font-mono text-xs text-tan font-semibold">
                          {opt.style}
                        </span>
                      </div>
                      <button
                        onClick={() => copyToClipboard(opt.rewritten_text, idx)}
                        className={`font-mono text-xs px-2.5 py-1 rounded transition-all flex items-center gap-1.5 focus:outline-none ${
                          isCopied
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                            : "bg-white/5 hover:bg-white/10 text-tan hover:text-white border border-white/10"
                        }`}
                      >
                        {isCopied ? (
                          <>
                            <span>✓</span>
                            <span>{isHinglish ? "Copied!" : "Copied!"}</span>
                          </>
                        ) : (
                          <>
                            <span>📋</span>
                            <span>
                              {isHinglish ? "Copy Line" : "Copy Bullet"}
                            </span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* Rewritten Text Box */}
                    <div className="p-2.5 rounded bg-black/40 border border-white/5 font-mono text-xs text-paper leading-relaxed mb-2 select-text">
                      • {opt.rewritten_text}
                    </div>

                    {/* Explanation */}
                    <p className="font-mono text-[11px] text-tan-dim leading-snug">
                      <span className="text-amber-400/80 mr-1">
                        💡 Why it works:
                      </span>
                      {opt.explanation}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-white/10 bg-[#161410] flex items-center justify-between text-tan-dim font-mono text-[11px]">
          <span>
            Tip: Star bullets with action verbs & measurable % / $ outcomes.
          </span>
          <button
            onClick={onClose}
            className="hover:text-white transition-colors underline"
          >
            {isHinglish ? "Band Karein" : "Close"}
          </button>
        </div>
      </div>
    </div>
  );
}
