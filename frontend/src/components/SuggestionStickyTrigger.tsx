import { useState, useEffect } from "react";
import SuggestionModal from "./SuggestionModal";

export default function SuggestionStickyTrigger() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasSeenResult, setHasSeenResult] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    // Check if user has viewed at least one result
    try {
      const seen =
        localStorage.getItem("resumeroast_has_seen_result") === "true";
      const hasRecentRoast = Boolean(
        localStorage.getItem("resumeroast_last_id"),
      );
      if (seen || hasRecentRoast) {
        setHasSeenResult(true);
      }
    } catch {}

    // Listen for custom open event triggered by footer or other buttons
    const handleOpenEvent = () => setIsOpen(true);
    window.addEventListener("open-suggestion-box", handleOpenEvent);
    return () =>
      window.removeEventListener("open-suggestion-box", handleOpenEvent);
  }, []);

  // If user hasn't seen any result yet and not dismissed, don't show floating sticky note
  // But modal can still be triggered by footer
  return (
    <>
      {hasSeenResult && !isDismissed && (
        <aside
          aria-label="Suggestion Box"
          className="fixed bottom-5 right-5 z-40 animate-paper-settle group"
          style={{ "--paper-rotate": "-2.5deg" } as React.CSSProperties}
        >
          {/* Handwritten Sticky Note Button */}
          <div className="relative">
            {/* Tiny close button to dismiss sticky note */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setIsDismissed(true);
              }}
              className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-stone-900/80 text-stone-300 hover:text-white border border-white/20 text-[10px] flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
              title="Dismiss sticky note"
            >
              ✕
            </button>

            {/* Sticky Note Body */}
            <button
              type="button"
              onClick={() => setIsOpen(true)}
              className="bg-[#FEF08A] hover:bg-[#FDE047] text-stone-900 px-3.5 py-2 rounded-sm shadow-xl border border-amber-300/60 flex items-center gap-2 transform hover:-translate-y-0.5 hover:rotate-0 transition-all cursor-pointer select-none"
            >
              {/* Paper tape visual accent */}
              <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-2.5 bg-amber-100/60 border border-amber-300/40 rotate-[1deg] pointer-events-none" />
              <span className="text-base">💡</span>
              <span className="font-handwritten text-lg font-bold tracking-wide">
                Got an idea?
              </span>
            </button>
          </div>
        </aside>
      )}

      {/* Global Suggestion Modal */}
      <SuggestionModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}

/** Helper utility to open the suggestion box from anywhere (e.g. Footer) */
export function openSuggestionBox() {
  window.dispatchEvent(new CustomEvent("open-suggestion-box"));
}
