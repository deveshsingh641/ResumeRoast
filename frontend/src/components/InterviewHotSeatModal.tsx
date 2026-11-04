import React, { useState, useEffect } from "react";
import axios from "axios";
import { useTranslation } from "react-i18next";
import { normalizeLang } from "@/i18n/detector";

interface StarFramework {
  situation_task: string;
  action: string;
  result: string;
}

interface InterviewQuestion {
  id: number;
  flaw_reference: string;
  category: string;
  difficulty: "Crucial" | "Tough" | "Brutal" | string;
  question: string;
  interviewer_trap: string;
  rookie_blunder: string;
  star_framework: StarFramework;
  script_to_say: string;
}

interface InterviewPrepData {
  roast_id: string;
  candidate_summary: string;
  questions: InterviewQuestion[];
  source: string;
}

interface InterviewHotSeatModalProps {
  isOpen: boolean;
  onClose: () => void;
  roastId: string;
}

export default function InterviewHotSeatModal({
  isOpen,
  onClose,
  roastId,
}: InterviewHotSeatModalProps) {
  const { i18n } = useTranslation();
  const isHinglish = normalizeLang(i18n.language) === "hi-IN";

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<InterviewPrepData | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Fetch interview prep questions when opened
  useEffect(() => {
    if (!isOpen) {
      if (typeof window !== "undefined" && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
      return;
    }

    const fetchPrep = async () => {
      try {
        setLoading(true);
        const { data: res } = await axios.get(
          `/api/roast/${roastId}/interview-prep`,
          {
            headers: { "Accept-Language": isHinglish ? "hi-IN" : "en" },
            timeout: 20000,
          },
        );
        if (res && res.data) {
          setData(res.data);
        }
      } catch (err) {
        // Fallback default structure if network or server issue
        setData({
          roast_id: roastId,
          candidate_summary:
            "Interviewers will aggressively probe your metrics, individual ownership, and architectural trade-offs.",
          source: "fallback",
          questions: [
            {
              id: 1,
              flaw_reference: "Vague team contributions without metrics",
              category: "Metrics & Impact Probe",
              difficulty: "Brutal",
              question:
                "You mentioned working on core backend services. What was the exact throughput or latency requirement, and what was the single hardest bug you personally diagnosed and fixed in production?",
              interviewer_trap:
                "They are testing if you personally understand the systems and wrote the code, or if you were just a passive team passenger.",
              rookie_blunder:
                "Saying 'Our team handled it and we didn't track numbers' — immediate red flag for hiring managers.",
              star_framework: {
                situation_task:
                  "Our API endpoint degraded to >800ms during marketing peak loads.",
                action:
                  "I instrumented APM tracing, indexed hot foreign keys, and decoupled blocking queries into asynchronous Celery tasks.",
                result:
                  "Cut p95 latency from 820ms to 110ms and scaled through peak traffic with zero dropped requests.",
              },
              script_to_say:
                "During peak traffic, our query latency spiked to 800ms. I traced the bottleneck using query plans, added compound indexing, and cached read-heavy summaries in Redis, reducing latency to 110ms and preventing downtime.",
            },
            {
              id: 2,
              flaw_reference: "Generic buzzwords and collaboration claims",
              category: "Ownership & Conflict",
              difficulty: "Tough",
              question:
                "Tell me about a time you had a technical disagreement with a senior engineer or product lead on an architecture choice. How did you resolve it?",
              interviewer_trap:
                "They test whether you can use benchmarks and data to build technical alignment without ego or passive resistance.",
              rookie_blunder:
                "Saying 'We never had disagreements' — shows lack of technical conviction or ownership.",
              star_framework: {
                situation_task:
                  "Product wanted real-time synchronous audit writes on every payment mutation.",
                action:
                  "I ran benchmark load tests proving it doubled transaction response times, then proposed an asynchronous event queue architecture instead.",
                result:
                  "Preserved audit compliance while keeping API response times strictly under 95ms.",
              },
              script_to_say:
                "When product requested synchronous database logging for every event, I benchmarked the overhead and showed it would degrade throughput by 40%. I proposed an asynchronous message queue solution that met both audit needs and our SLA.",
            },
            {
              id: 3,
              flaw_reference: "Tech stack breadth vs depth",
              category: "System Design & Trade-offs",
              difficulty: "Crucial",
              question:
                "What is the single biggest architectural bottleneck of the tech stack you built with, and if traffic multiplied by 10x tomorrow, what breaks first?",
              interviewer_trap:
                "Differentiates junior engineers from senior bar-raisers. True engineers know every architectural choice has trade-offs.",
              rookie_blunder:
                "Claiming 'Our architecture has no weaknesses and scales infinitely.'",
              star_framework: {
                situation_task:
                  "High concurrent traffic caused connection pool exhaustion in our primary database.",
                action:
                  "Introduced PgBouncer connection pooling and migrated analytical queries to read-replicas.",
                result:
                  "Sustained 5x concurrent user spikes with zero connection drops and 99.95% uptime.",
              },
              script_to_say:
                "The primary bottleneck was database connection pool exhaustion under sudden spikes. At 10x load, I would implement connection pooling with read replicas and move hot read paths to Redis.",
            },
          ],
        });
      } finally {
        setLoading(false);
      }
    };

    fetchPrep();
  }, [isOpen, roastId, isHinglish]);

  // Speech synthesis for realistic interviewer voice
  const handleSpeakQuestion = (text: string) => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.92;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const handleCopyScript = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {}
  };

  if (!isOpen) return null;

  const currentQ = data?.questions?.[activeTab];

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#14100C] border border-white/[0.12] rounded-sm p-5 sm:p-7 shadow-2xl relative max-h-[92vh] overflow-y-auto text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-tan-dim hover:text-paper font-mono text-xl p-1 transition-colors"
          aria-label="Close hot seat"
        >
          ✕
        </button>

        {/* Header */}
        <div className="mb-5 border-b border-white/[0.08] pb-4 pr-8">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-widest bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-sm">
              {isHinglish
                ? "INTERVIEW HOT-SEAT // TAIYARI KARO"
                : "AI INTERVIEW HOT-SEAT // SURVIVAL DRILL"}
            </span>
            <span className="font-mono text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-sm border border-emerald-500/20">
              STAR Method Ready
            </span>
          </div>
          <h2 className="font-display text-xl sm:text-2xl text-paper">
            {isHinglish
              ? "Recruiter Trap Questions & STAR Scripts 🔥"
              : "Recruiter Trap Questions & Winning Scripts 🔥"}
          </h2>
          <p className="font-mono text-xs text-tan-dim mt-1.5 leading-relaxed">
            {data?.candidate_summary ||
              "Based on your resume flaws, interviewers will challenge you with these questions to verify your depth."}
          </p>
        </div>

        {loading ? (
          <div className="py-12 text-center font-mono text-xs text-tan-dim space-y-3">
            <div className="w-8 h-8 border-2 border-amber-400 border-t-transparent rounded-full animate-spin mx-auto" />
            <p>
              Analyzing resume flaws & synthesizing interview trap questions...
            </p>
          </div>
        ) : currentQ ? (
          <div>
            {/* Tabs */}
            <div className="flex items-center gap-2 mb-5 overflow-x-auto pb-1 border-b border-white/[0.06]">
              {data?.questions.map((q, idx) => (
                <button
                  key={q.id}
                  onClick={() => {
                    setActiveTab(idx);
                    setShowAnswer(false);
                    if (
                      typeof window !== "undefined" &&
                      window.speechSynthesis
                    ) {
                      window.speechSynthesis.cancel();
                      setIsSpeaking(false);
                    }
                  }}
                  className={`font-mono text-xs px-3 py-1.5 rounded-sm border transition-all whitespace-nowrap flex items-center gap-1.5 ${
                    activeTab === idx
                      ? "bg-amber-500/20 border-amber-500/40 text-amber-300 font-bold"
                      : "bg-white/[0.02] border-white/[0.08] text-tan-dim hover:text-paper hover:border-white/[0.18]"
                  }`}
                >
                  <span>
                    Q{idx + 1}: {q.category}
                  </span>
                  <span
                    className={`text-[9px] px-1 py-0.2 rounded-xs uppercase ${
                      q.difficulty === "Brutal"
                        ? "bg-red-500/20 text-red-300"
                        : q.difficulty === "Tough"
                          ? "bg-amber-500/20 text-amber-300"
                          : "bg-cyan-500/20 text-cyan-300"
                    }`}
                  >
                    {q.difficulty}
                  </span>
                </button>
              ))}
            </div>

            {/* Target Flaw Trigger */}
            <div className="mb-4 bg-red-950/20 border border-red-500/20 rounded-sm p-3">
              <span className="font-mono text-[10px] text-red-400 font-bold uppercase tracking-wider block mb-1">
                ⚠️ TRIGGERED BY RESUME FLAW:
              </span>
              <p className="font-mono text-xs text-red-200/90 italic">
                "{currentQ.flaw_reference}"
              </p>
            </div>

            {/* The Hard Question */}
            <div className="mb-5 bg-[#1a1410] border border-white/[0.1] rounded-sm p-4 relative">
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold">
                  THE PROBING QUESTION
                </span>
                <button
                  onClick={() => handleSpeakQuestion(currentQ.question)}
                  className="font-mono text-[11px] text-tan-dim hover:text-paper bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.1] px-2 py-0.5 rounded-sm flex items-center gap-1 transition-colors"
                  title="Listen to interviewer"
                >
                  <span>
                    {isSpeaking ? "⏹ Stop Voice" : "🎙️ Hear Interviewer"}
                  </span>
                </button>
              </div>
              <p className="font-display text-base sm:text-lg text-paper leading-snug">
                "{currentQ.question}"
              </p>
            </div>

            {/* Dual Insights: Trap & Blunder */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
              <div className="bg-black/30 border border-white/[0.06] rounded-sm p-3">
                <span className="font-mono text-[10px] text-cyan-400 font-bold uppercase tracking-wider block mb-1">
                  🕵️ WHY THEY ASK THIS (THE TRAP)
                </span>
                <p className="font-mono text-xs text-tan-dim leading-relaxed">
                  {currentQ.interviewer_trap}
                </p>
              </div>
              <div className="bg-black/30 border border-red-500/15 rounded-sm p-3">
                <span className="font-mono text-[10px] text-red-400 font-bold uppercase tracking-wider block mb-1">
                  🚫 ROOKIE BLUNDER (DO NOT SAY)
                </span>
                <p className="font-mono text-xs text-tan-dim leading-relaxed">
                  {currentQ.rookie_blunder}
                </p>
              </div>
            </div>

            {/* Answer Reveal Button */}
            {!showAnswer ? (
              <div className="text-center py-2">
                <button
                  onClick={() => setShowAnswer(true)}
                  className="w-full py-3 px-4 rounded-sm bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-black font-mono font-bold text-xs uppercase tracking-wider transition-all shadow-lg hover:shadow-amber-500/20"
                >
                  🔓 Reveal Model STAR Answer & Spoken Script
                </button>
              </div>
            ) : (
              <div className="space-y-4 animate-in fade-in duration-300">
                {/* STAR Breakdown */}
                <div className="bg-[#121612] border border-emerald-500/30 rounded-sm p-4">
                  <span className="font-mono text-[10px] text-emerald-400 font-bold uppercase tracking-widest block mb-2">
                    🎯 STAR RESPONSE FRAMEWORK
                  </span>
                  <div className="space-y-2 text-xs font-mono">
                    <div className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold min-w-[3.5rem] uppercase text-[10px]">
                        [S / T]:
                      </span>
                      <span className="text-paper/90">
                        {currentQ.star_framework.situation_task}
                      </span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold min-w-[3.5rem] uppercase text-[10px]">
                        [Action]:
                      </span>
                      <span className="text-paper/90">
                        {currentQ.star_framework.action}
                      </span>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold min-w-[3.5rem] uppercase text-[10px]">
                        [Result]:
                      </span>
                      <span className="text-emerald-300 font-bold">
                        {currentQ.star_framework.result}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Spoken Script */}
                <div className="bg-black/50 border border-white/[0.1] rounded-sm p-4 relative">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold">
                      🗣️ EXACT SPOKEN SCRIPT (SAY THIS OUT LOUD)
                    </span>
                    <button
                      onClick={() => handleCopyScript(currentQ.script_to_say)}
                      className="font-mono text-[10px] text-amber-300 hover:text-amber-200 border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 rounded-sm transition-colors"
                    >
                      {copied ? "✓ Copied Script!" : "📋 Copy Script"}
                    </button>
                  </div>
                  <p className="font-mono text-xs text-paper leading-relaxed italic">
                    "{currentQ.script_to_say}"
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-10 text-center font-mono text-xs text-tan-dim space-y-2">
            <p className="text-paper">
              {isHinglish
                ? "Is resume ke liye koi interview traps generate nahi huye."
                : "No interview trap questions generated for this report."}
            </p>
            <p>
              {isHinglish
                ? "Aapke bullet points clear aur direct lag rahe hain."
                : "Your accomplishments appear direct and well-structured."}
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-white/[0.08] flex items-center justify-between font-mono text-[11px] text-tan-dim">
          <span>Practice these scripts before your next interview round.</span>
          <button
            onClick={onClose}
            className="text-tan hover:text-paper underline"
          >
            Close Drill
          </button>
        </div>
      </div>
    </div>
  );
}
