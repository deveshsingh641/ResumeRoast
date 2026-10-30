import { useState, useRef, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import { useAppStore } from "@/store/useAppStore";
import AuthModal from "@/components/AuthModal";

interface UserAccountNavProps {
  className?: string;
  compact?: boolean;
}

export default function UserAccountNav({
  className = "",
  compact = false,
}: UserAccountNavProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const navigate = useNavigate();

  const { userEmail, usage, logout } = useAppStore();
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isPro = usage?.is_pro ?? false;

  // Mask email for display: e.g. ank***@gmail.com
  const displayEmail = userEmail
    ? (() => {
        const parts = userEmail.split("@");
        if (parts.length === 2) {
          const name = parts[0];
          const maskedName =
            name.length > 3
              ? name.slice(0, 3) + "***"
              : name.slice(0, 1) + "***";
          return `${maskedName}@${parts[1]}`;
        }
        return userEmail;
      })()
    : null;

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [dropdownOpen]);

  // Listen for global open-auth-modal event
  useEffect(() => {
    const handleOpenAuth = () => setShowAuthModal(true);
    window.addEventListener("open-auth-modal", handleOpenAuth);
    return () => {
      window.removeEventListener("open-auth-modal", handleOpenAuth);
    };
  }, []);

  return (
    <>
      <div className={`relative inline-block ${className}`} ref={dropdownRef}>
        {!userEmail ? (
          /* Sign In Button */
          <button
            type="button"
            onClick={() => setShowAuthModal(true)}
            className="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-sm bg-white/5 hover:bg-white/10 text-paper border border-white/15 text-[11px] sm:text-xs font-mono font-medium transition cursor-pointer shrink-0"
            title="Sign in with your email to sync Pro plan"
          >
            <span>👤</span>
            <span className="font-bold">
              {isHinglish ? "Sign In" : "Sign In"}
            </span>
          </button>
        ) : (
          /* Logged In User Pill */
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className={`inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-1 sm:py-1.5 rounded-sm font-mono text-[11px] sm:text-xs transition cursor-pointer shrink-0 border ${
              isPro
                ? "bg-amber-500/15 border-amber-500/40 text-amber-300 hover:bg-amber-500/25 shadow-sm shadow-amber-950/30"
                : "bg-white/5 border-white/15 text-stone-300 hover:bg-white/10"
            }`}
          >
            {isPro ? (
              <span className="flex items-center gap-1 font-bold">
                <span>👑</span>
                <span>PRO</span>
              </span>
            ) : (
              <span>👤</span>
            )}
            <span className="max-w-[120px] truncate hidden sm:inline">
              {displayEmail}
            </span>
            <span className="text-[9px] text-stone-400">▾</span>
          </button>
        )}

        {/* Dropdown Menu */}
        {dropdownOpen && userEmail && (
          <div className="absolute right-0 mt-2 w-64 bg-[#181412] border border-white/20 rounded-md shadow-2xl z-50 p-3 text-left font-mono animate-fadeIn">
            <div className="pb-2 mb-2 border-b border-white/10">
              <div className="text-[10px] text-tan-dim uppercase tracking-wider font-bold">
                {isHinglish ? "Account Email" : "Account Email"}
              </div>
              <div className="text-xs text-white font-bold truncate mt-0.5">
                {userEmail}
              </div>
              <div className="mt-1 flex items-center gap-1.5">
                {isPro ? (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                    👑 Lifetime / Pro Active
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-stone-300 border border-white/15">
                    Free Tier (1 roast/day)
                  </span>
                )}
              </div>
            </div>

            <div className="space-y-1.5">
              {!isPro && (
                <Link
                  to="/pricing"
                  onClick={() => setDropdownOpen(false)}
                  className="block w-full py-1.5 px-2 rounded text-xs font-bold bg-[#E8422D]/20 hover:bg-[#E8422D]/30 text-[#FF6347] border border-[#E8422D]/40 text-center transition"
                >
                  ⚡{" "}
                  {isHinglish ? "Upgrade to Pro (₹99)" : "Upgrade to Pro (₹99)"}
                </Link>
              )}

              <Link
                to="/roast"
                onClick={() => setDropdownOpen(false)}
                className="block w-full py-1.5 px-2 rounded text-xs text-stone-300 hover:text-white hover:bg-white/5 transition"
              >
                🔥 {isHinglish ? "New Resume Roast" : "New Resume Roast"}
              </Link>

              <Link
                to="/match"
                onClick={() => setDropdownOpen(false)}
                className="block w-full py-1.5 px-2 rounded text-xs text-stone-300 hover:text-white hover:bg-white/5 transition"
              >
                🎯 {isHinglish ? "JD Match" : "Job Match"}
              </Link>

              <button
                type="button"
                onClick={() => {
                  logout();
                  setDropdownOpen(false);
                }}
                className="w-full text-left py-1.5 px-2 rounded text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition cursor-pointer"
              >
                🚪 {isHinglish ? "Log Out" : "Log Out"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </>
  );
}
