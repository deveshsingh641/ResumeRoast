import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";
import type { Issue } from "@/store/useAppStore";

interface DimensionalScorecardProps {
  overallScore: number;
  issues: Issue[];
  className?: string;
}

interface Dimension {
  id: string;
  label: string;
  score: number;
  icon: string;
  status: "critical" | "warning" | "solid" | "elite";
  tip: string;
  tipHi: string;
}

export default function DimensionalScorecard({
  overallScore,
  issues,
  className = "",
}: DimensionalScorecardProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  // Derive dimensional scores from issues and overall score
  const noMetricsCount = issues.filter(
    (i) => i.category === "no-metrics",
  ).length;
  const buzzwordCount = issues.filter((i) => i.category === "buzzword").length;
  const formattingCount = issues.filter(
    (i) => i.category === "formatting" || i.category === "length",
  ).length;
  const typoCount = issues.filter((i) => i.category === "typo").length;

  // 1. Metrics Score
  const metricScore = Math.max(
    18,
    Math.min(95, Math.round(overallScore * 0.7 + (4 - noMetricsCount) * 7)),
  );
  // 2. Action Verb Score
  const actionVerbScore = Math.max(
    25,
    Math.min(96, Math.round(overallScore * 0.8 + 10 - noMetricsCount * 5)),
  );
  // 3. ATS Scannability
  const atsScore = Math.max(
    30,
    Math.min(98, Math.round(92 - formattingCount * 18 - typoCount * 12)),
  );
  // 4. Buzzword / Fluff Index (100 = cleanest, 0 = pure jargon)
  const fluffScore = Math.max(
    20,
    Math.min(95, Math.round(90 - buzzwordCount * 22)),
  );
  // 5. Tech Stack Proof
  const techScore = Math.max(
    35,
    Math.min(97, Math.round(overallScore * 0.85 + 15)),
  );

  const getStatus = (score: number): Dimension["status"] => {
    if (score < 45) return "critical";
    if (score < 70) return "warning";
    if (score < 88) return "solid";
    return "elite";
  };

  const dimensions: Dimension[] = [
    {
      id: "metrics",
      label: isHinglish
        ? "Metric Density (Numbers)"
        : "Quantified Impact & Metrics",
      score: metricScore,
      icon: "📊",
      status: getStatus(metricScore),
      tip: "Include %, $, scale (req/sec), and before/after numbers in every work experience bullet point.",
      tipHi:
        "Har bullet point mein % growth, latency reduction ya user scale ke numbers add karo.",
    },
    {
      id: "verbs",
      label: isHinglish
        ? "Action Verb Power"
        : "Action Verb & Leadership Strength",
      score: actionVerbScore,
      icon: "⚡",
      status: getStatus(actionVerbScore),
      tip: "Replace passive phrases like 'assisted with' or 'responsible for' with 'architected', 'spearheaded', or 'orchestrated'.",
      tipHi:
        "'Assisted' ya 'responsible for' hatakar strong action verbs jaise 'Architected' ya 'Spearheaded' lagao.",
    },
    {
      id: "ats",
      label: isHinglish
        ? "ATS Readability & Format"
        : "ATS Parsing & Format Scannability",
      score: atsScore,
      icon: "🤖",
      status: getStatus(atsScore),
      tip: "Clean single-column structure with standard section headers ensures 99%+ ATS parser accuracy.",
      tipHi:
        "Standard headers aur clean layout rakhein taaki automated ATS scanner fail na ho.",
    },
    {
      id: "fluff",
      label: isHinglish
        ? "Brevity & Fluff Filter"
        : "Buzzword & Fluff-Free Index",
      score: fluffScore,
      icon: "🎯",
      status: getStatus(fluffScore),
      tip: "Eliminate corporate clichés ('hardworking team player', 'synergistic'). Replace with concrete technical accomplishments.",
      tipHi:
        "Ghise-pite generic words hatakar real projects aur concrete deliverables par focus karo.",
    },
    {
      id: "tech",
      label: isHinglish
        ? "Tech Stack Clarity"
        : "Technical Stack Proof & Depth",
      score: techScore,
      icon: "💻",
      status: getStatus(techScore),
      tip: "Name specific versions, frameworks, cloud providers, and databases in context rather than just a loose list.",
      tipHi:
        "Frameworks aur databases ko project context ke saath likho sirf loose comma-separated list mat banao.",
    },
  ];

  const statusColors = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    solid: "bg-cyan-500/20 text-cyan-300 border-cyan-500/30",
    elite: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  };

  const barColors = {
    critical: "bg-gradient-to-r from-red-600 to-red-400",
    warning: "bg-gradient-to-r from-amber-600 to-amber-400",
    solid: "bg-gradient-to-r from-cyan-600 to-cyan-400",
    elite: "bg-gradient-to-r from-emerald-600 to-emerald-400",
  };

  const statusLabels = {
    critical: isHinglish ? "CRITICAL // SUDHAR ZAROORI" : "CRITICAL RISK",
    warning: isHinglish ? "AVERAGE // SCOPE HAI" : "NEEDS WORK",
    solid: isHinglish ? "SOLID // THEEK HAI" : "STRONG",
    elite: isHinglish ? "ELITE // SHANDAR" : "ELITE ATS",
  };

  return (
    <div
      className={`w-full max-w-[640px] mx-auto bg-gradient-to-b from-[#181410] to-[#120F0C] border border-white/[0.08] rounded-sm p-5 sm:p-6 text-left relative overflow-hidden shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-4 border-b border-white/[0.08] pb-3">
        <div>
          <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold block">
            {isHinglish
              ? "DIAGNOSTIC AUDIT // 5 KEY VECTORS"
              : "DIAGNOSTIC AUDIT // 5 KEY DIMENSIONS"}
          </span>
          <h3 className="font-display text-lg sm:text-xl text-paper">
            {isHinglish
              ? "Resume Health Scorecard 🔬"
              : "Resume Health Scorecard 🔬"}
          </h3>
        </div>
        <div className="text-right">
          <span className="font-mono text-[10px] text-tan-dim block uppercase">
            ATS Readability
          </span>
          <span className="font-mono text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 border border-emerald-500/20 rounded-sm">
            {atsScore}% Pass
          </span>
        </div>
      </div>

      <p className="font-mono text-xs text-tan-dim mb-5 leading-relaxed">
        {isHinglish
          ? "Recruiter ATS algorithms aur senior interviewers aapka resume in 5 dimensions par judge karte hain:"
          : "Hiring managers and modern ATS algorithms grade your resume across these 5 core dimensions:"}
      </p>

      {/* Dimension Bars */}
      <div className="space-y-4">
        {dimensions.map((dim) => {
          const isExpanded = expandedDim === dim.id;
          return (
            <div
              key={dim.id}
              className="bg-black/30 border border-white/[0.05] rounded-sm p-3 hover:border-white/[0.12] transition-colors cursor-pointer"
              onClick={() => setExpandedDim(isExpanded ? null : dim.id)}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-base" aria-hidden="true">
                    {dim.icon}
                  </span>
                  <span className="font-mono text-xs text-paper font-medium">
                    {dim.label}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`font-mono text-[9px] uppercase px-1.5 py-0.5 rounded-sm border ${
                      statusColors[dim.status]
                    }`}
                  >
                    {statusLabels[dim.status]}
                  </span>
                  <span className="font-mono text-xs font-bold text-paper min-w-[2.5rem] text-right">
                    {dim.score}/100
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 bg-white/[0.06] rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ease-out ${
                    barColors[dim.status]
                  }`}
                  style={{ width: `${dim.score}%` }}
                />
              </div>

              {/* Actionable tip (expandable or default subtle) */}
              <div
                className={`mt-2 font-mono text-[11px] text-tan-dim border-t border-white/[0.04] pt-2 flex items-start gap-1.5 transition-all ${
                  isExpanded ? "block text-tan" : "hidden sm:flex"
                }`}
              >
                <span className="text-amber-400 font-bold">💡 Fix:</span>
                <span>{isHinglish ? dim.tipHi : dim.tip}</span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] font-mono text-tan-dim">
        <span>Click any metric to inspect fix recommendations</span>
        <span className="text-amber-400">Target Benchmark: 85+</span>
      </div>
    </div>
  );
}
