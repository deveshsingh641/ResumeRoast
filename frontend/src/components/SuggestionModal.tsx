import React, { useState, useEffect } from "react";
import axios from "axios";

interface SuggestionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type CategoryType = "feature" | "bug" | "feedback" | "other";

const CATEGORIES: { id: CategoryType; label: string; icon: string }[] = [
  { id: "feature", label: "Feature Idea", icon: "💡" },
  { id: "bug", label: "Bug Report", icon: "🐛" },
  { id: "feedback", label: "Feedback", icon: "💬" },
  { id: "other", label: "Something Else", icon: "✨" },
];

export default function SuggestionModal({
  isOpen,
  onClose,
}: SuggestionModalProps) {
  const [text, setText] = useState("");
  const [category, setCategory] = useState<CategoryType>("feature");
  const [email, setEmail] = useState("");
  const [website, setWebsite] = useState(""); // Honeypot field for bot defense
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  // Pre-fill email from localStorage if available
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
    const cleanText = text.trim();

    if (cleanText.length < 3) {
      setStatus("error");
      setMessage(
        "Please enter at least a few words so we understand your thought.",
      );
      return;
    }

    try {
      setLoading(true);
      setStatus("idle");
      setMessage(null);

      if (email.trim()) {
        try {
          localStorage.setItem(
            "resumeroast_user_email",
            email.trim().toLowerCase(),
          );
        } catch {}
      }

      const { data } = await axios.post("/api/suggestions", {
        text: cleanText,
        category,
        email: email.trim() || undefined,
        website: website.trim() || undefined, // Honeypot
      });

      setStatus("success");
      setMessage(data.message || "Got it, thanks! 🙌 We actually read these.");
      setText("");
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : err?.message || "Failed to submit. Please try again.";
      setStatus("error");
      setMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-[#1C1814] border border-amber-400/30 rounded-lg p-6 sm:p-8 max-w-[540px] w-full text-left relative shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Paper tape decoration at top */}
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-28 h-6 bg-amber-200/20 border-b border-amber-300/30 rotate-[-1deg] pointer-events-none" />

        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-tan-dim hover:text-paper font-mono text-lg transition-colors p-1"
          aria-label="Close modal"
        >
          ✕
        </button>

        {status === "success" ? (
          <div className="text-center py-6 space-y-4">
            <div className="text-4xl animate-bounce">🙌</div>
            <h3 className="font-display text-2xl text-paper tracking-tight">
              Suggestion Logged!
            </h3>
            <p className="font-mono text-sm text-emerald-400 max-w-sm mx-auto leading-relaxed">
              {message}
            </p>
            <p className="font-handwritten text-xl text-amber-300 rotate-[-1deg]">
              "Founder's desk par note chipka diya hai 📝"
            </p>
            <div className="pt-3">
              <button
                type="button"
                onClick={onClose}
                className="px-6 py-2.5 rounded text-xs font-mono font-bold bg-[#E8422D] hover:bg-[#D43723] text-paper transition-colors"
              >
                Back to Desk
              </button>
            </div>
          </div>
        ) : (
          <div>
            {/* Header */}
            <div className="flex items-center gap-2 mb-1">
              <span className="text-amber-400 text-lg">💡</span>
              <span className="section-label">FOUNDER SUGGESTION BOX</span>
            </div>
            <h3 className="font-display text-2xl sm:text-3xl text-paper tracking-tight mb-2">
              What's on your mind?
            </h3>
            <p className="font-mono text-xs text-tan-dim mb-5 leading-relaxed">
              Feature ideas, feedback, edge-cases, or general thoughts. We read
              every single one to shape what gets built next.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Category Pills */}
              <div>
                <label className="block font-mono text-[11px] text-tan-dim uppercase mb-2">
                  Category (Optional)
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {CATEGORIES.map((cat) => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setCategory(cat.id)}
                      className={`px-2.5 py-1.5 rounded text-xs font-mono flex items-center justify-center gap-1.5 border transition-all ${
                        category === cat.id
                          ? "bg-amber-400/20 border-amber-400 text-amber-300 font-bold"
                          : "bg-black/30 border-white/10 text-stone-400 hover:border-white/25 hover:text-tan"
                      }`}
                    >
                      <span>{cat.icon}</span>
                      <span className="truncate">{cat.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Main Textarea */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="suggestion-text"
                    className="font-mono text-[11px] text-tan uppercase"
                  >
                    Your Thought <span className="text-stamp">*</span>
                  </label>
                  <span className="font-mono text-[10px] text-stone-500">
                    {text.length}/2000
                  </span>
                </div>
                <textarea
                  id="suggestion-text"
                  required
                  rows={4}
                  maxLength={2000}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Kuch naya idea hai? e.g. 'Add LinkedIn job matcher' or 'Give an option to edit bullet rewrites directly' 💭"
                  className="w-full bg-black/50 border border-white/15 focus:border-amber-400 rounded p-3 font-mono text-xs text-paper placeholder:text-stone-600 focus:outline-none transition-colors resize-none leading-relaxed"
                />
              </div>

              {/* Optional Email */}
              <div>
                <label
                  htmlFor="suggestion-email"
                  className="block font-mono text-[11px] text-tan-dim uppercase mb-1"
                >
                  Your Email{" "}
                  <span className="text-stone-500 lowercase">
                    (optional — only if you'd like a follow-up)
                  </span>
                </label>
                <input
                  id="suggestion-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@domain.com"
                  className="w-full bg-black/50 border border-white/15 focus:border-amber-400 rounded px-3 py-2 font-mono text-xs text-paper placeholder:text-stone-600 focus:outline-none transition-colors"
                />
              </div>

              {/* Anti-spam Honeypot (hidden from human users) */}
              <input
                type="text"
                name="website"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                tabIndex={-1}
                autoComplete="off"
                className="hidden opacity-0 pointer-events-none absolute -left-[9999px]"
                aria-hidden="true"
              />

              {/* Error Alert */}
              {status === "error" && message && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-xs font-mono text-red-300">
                  ⚠️ {message}
                </div>
              )}

              {/* Actions */}
              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={loading || text.trim().length < 3}
                  className="w-full sm:w-auto flex-1 px-5 py-2.5 rounded text-xs font-mono font-bold bg-[#E8422D] hover:bg-[#D43723] disabled:opacity-50 text-paper transition-all shadow-md flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Sending note...</span>
                    </>
                  ) : (
                    <>
                      <span>Send to Founder Desk</span>
                      <span>🚀</span>
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={onClose}
                  className="w-full sm:w-auto px-4 py-2.5 rounded text-xs font-mono text-tan-dim hover:text-paper border border-white/10 hover:border-white/20 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
