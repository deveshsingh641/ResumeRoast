import { useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";

export default function PlacementSeasonBanner() {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const currentMonth = new Date().getMonth(); // 0 = Jan, 7 = Aug, 11 = Dec
  const isPlacementSeason = currentMonth >= 7 && currentMonth <= 11; // Aug-Dec

  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem("dismiss_placement_banner") === "true";
    } catch {
      return false;
    }
  });

  if (!isPlacementSeason || dismissed) {
    return null;
  }

  const handleDismiss = () => {
    setDismissed(true);
    try {
      sessionStorage.setItem("dismiss_placement_banner", "true");
    } catch {
      // Ignore
    }
  };

  return (
    <aside
      className="bg-gradient-to-r from-amber-950/80 via-black to-red-950/80 border-b border-amber-500/30 px-4 py-2 text-center relative z-30"
      aria-label="Campus Placement Season Alert"
    >
      <div className="max-w-[960px] mx-auto flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2 text-paper text-left flex-1 min-w-0">
          <span className="text-amber-400 font-bold animate-pulse shrink-0">
            🎯
          </span>
          <p className="font-mono leading-tight text-xs">
            <strong className="text-amber-300">
              {isHinglish ? "Placement season chal raha hai" : "Hiring season is live"}
            </strong>{" "}
            {isHinglish ? "— resume ready hai ya jugaad se chal raha hai? 👀" : "— is your resume shortlist-ready or winging it? 👀"}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/roast"
            className="font-mono text-[11px] font-bold text-amber-300 hover:text-white bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 px-3 py-1 rounded-sm transition-colors whitespace-nowrap"
          >
            {isHinglish ? "Abhi check karwao →" : "Check Score Now →"}
          </Link>
          <button
            type="button"
            onClick={handleDismiss}
            aria-label="Dismiss placement season notification"
            className="text-tan-dim hover:text-paper font-mono text-sm px-1 leading-none select-none transition-colors"
          >
            ✕
          </button>
        </div>
      </div>
    </aside>
  );
}
