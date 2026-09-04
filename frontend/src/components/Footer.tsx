import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'

interface FooterProps {
  portfolioUrl?: string
  githubUrl?: string
  twitterUrl?: string
  linkedinUrl?: string
}

export default function Footer({
  portfolioUrl = 'https://github.com/deveshsingh641',
  githubUrl = 'https://github.com/deveshsingh641/ResumeRoast',
  twitterUrl = 'https://twitter.com',
  linkedinUrl = 'https://linkedin.com',
}: FooterProps) {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'
  const [copied, setCopied] = useState(false)

  const handleShare = async () => {
    const shareData = {
      title: 'ResumeRoast — Brutally Honest AI Resume Critique',
      text: isHinglish
        ? 'Bhai tera resume kaisa hai? AI desk pe daal ke roast check kar le 🔥'
        : 'Find out exactly what recruiters hate about your resume with AI red pen annotations 🔥',
      url: window.location.origin,
    }

    if (navigator.share) {
      try {
        await navigator.share(shareData)
        return
      } catch {
        // Fallback to clipboard
      }
    }

    try {
      await navigator.clipboard.writeText(window.location.origin)
      setCopied(true)
      setTimeout(() => setCopied(false), 2200)
    } catch {
      // ignore
    }
  }

  return (
    <footer className="border-t border-white/[0.08] bg-[#120F0C] pt-12 pb-8 px-4 sm:px-6 relative z-10 select-none">
      <div className="max-w-[1020px] mx-auto space-y-10">
        
        {/* ── Top Row: Brand + Creator Card ── */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center justify-between">
          
          {/* Brand & Mission (5 cols) */}
          <div className="md:col-span-5 text-center md:text-left space-y-3">
            <Link to="/" className="inline-block font-display text-lg sm:text-xl tracking-tight text-paper">
              RESUME<span className="text-stamp">ROAST</span>
              <span className="text-amber-400 font-mono text-[10px] ml-1.5">// 100% RAW</span>
            </Link>
            <p className="font-mono text-xs text-tan-dim leading-relaxed max-w-[360px] mx-auto md:mx-0">
              {isHinglish
                ? 'Resume roast — kyunki dost sach nahi bolte aur recruiters seedha reject kar dete hain. Desk kabhi jhooth nahi bolta.'
                : 'Brutally honest red pen annotations, zero sugarcoating, and metric-driven rewrites for high-growth tech talent.'}
            </p>
            <div className="flex items-center justify-center md:justify-start gap-2 pt-1">
              <span className="inline-flex items-center gap-1.5 font-mono text-[10px] px-2 py-0.5 bg-white/[0.04] border border-white/[0.08] rounded-full text-tan-dim">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {isHinglish ? 'Active & Open Source' : 'Active & Open Source'}
              </span>
            </div>
          </div>

          {/* Creator Spotlight Box (7 cols) */}
          <div className="md:col-span-7">
            <div className="bg-gradient-to-br from-[#1C1713] to-[#14100C] border border-white/[0.12] hover:border-amber-400/40 rounded-lg p-5 sm:p-6 shadow-xl transition-all duration-200">
              <div className="flex flex-col sm:flex-row items-center sm:items-start justify-between gap-4">
                
                {/* Creator Profile */}
                <div className="flex items-center gap-3.5 text-center sm:text-left">
                  <div className="relative shrink-0">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-stamp to-amber-400 flex items-center justify-center text-paper font-display text-lg shadow-md border-2 border-[#120F0C]">
                      DS
                    </div>
                    <span className="absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full bg-emerald-500 border-2 border-[#14100C]" title="Available for projects" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 justify-center sm:justify-start">
                      <span className="font-display text-sm sm:text-base text-paper">Devesh Singh</span>
                      <span className="font-mono text-[9px] uppercase px-1.5 py-0.2 bg-amber-400/10 border border-amber-400/30 text-amber-300 rounded-[2px]">
                        Creator
                      </span>
                    </div>
                    <p className="font-mono text-[11px] text-tan-dim mt-0.5">
                      {isHinglish ? 'Banaaya ☕ aur code ke saath' : 'Crafted with code, coffee & zero fluff'}
                    </p>
                  </div>
                </div>

                {/* Quick Share / Star Button */}
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={handleShare}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white/[0.06] hover:bg-white/[0.12] border border-white/10 rounded font-mono text-xs text-tan hover:text-paper transition-all"
                    title="Share project"
                  >
                    <span>{copied ? '✓ Copied!' : '🔗 Share'}</span>
                  </button>
                  <a
                    href={githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded font-mono text-xs text-amber-300 transition-all"
                  >
                    <span>⭐ Star</span>
                  </a>
                </div>
              </div>

              {/* Creator Social / Portfolio Links Row */}
              <div className="mt-4 pt-4 border-t border-white/[0.06] flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
                <span className="font-mono text-[10px] text-tan-dim uppercase tracking-wider mr-1">
                  Connect:
                </span>
                
                {/* Portfolio */}
                <a
                  href={portfolioUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.04] hover:bg-white/[0.09] hover:border-amber-400/40 border border-white/10 rounded-sm font-mono text-[11px] text-tan hover:text-amber-300 transition-colors"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                  <span>Portfolio</span>
                </a>

                {/* GitHub */}
                <a
                  href="https://github.com/deveshsingh641"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.04] hover:bg-white/[0.09] hover:border-white/30 border border-white/10 rounded-sm font-mono text-[11px] text-tan hover:text-paper transition-colors"
                >
                  <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                  <span>GitHub</span>
                </a>

                {/* Twitter / X */}
                <a
                  href="https://twitter.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.04] hover:bg-white/[0.09] hover:border-sky-400/40 border border-white/10 rounded-sm font-mono text-[11px] text-tan hover:text-sky-300 transition-colors"
                >
                  <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                  <span>Twitter / X</span>
                </a>

                {/* LinkedIn */}
                <a
                  href="https://linkedin.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.04] hover:bg-white/[0.09] hover:border-blue-400/40 border border-white/10 rounded-sm font-mono text-[11px] text-tan hover:text-blue-300 transition-colors"
                >
                  <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                    <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 10.9v8.37H9.2V10.9H6.46M7.83 6.45a1.63 1.63 0 1 0 0 3.26 1.63 1.63 0 0 0 0-3.26z" />
                  </svg>
                  <span>LinkedIn</span>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* ── Bottom Row: Navigation Links + Copyright ── */}
        <div className="pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
          
          <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 font-mono text-xs text-tan-dim" aria-label="Footer navigation">
            <Link to="/roast" className="hover:text-tan transition-colors">
              {isHinglish ? 'Resume Roast' : 'Grade Resume'}
            </Link>
            <Link to="/battle" className="hover:text-tan transition-colors">
              {isHinglish ? '⚔️ Battle Mode' : '⚔️ Battle Mode'}
            </Link>
            <Link to="/wall" className="hover:text-tan transition-colors">
              {isHinglish ? '🔥 Wall of Shame' : '🔥 Wall of Shame'}
            </Link>
            <Link to="/pricing" className="hover:text-tan transition-colors">
              {isHinglish ? 'Pricing' : 'Pricing'}
            </Link>
            <Link to="/privacy" className="hover:text-tan transition-colors">
              Privacy
            </Link>
            <Link to="/terms" className="hover:text-tan transition-colors">
              Terms
            </Link>
          </nav>

          <div className="font-mono text-xs text-tan-dim">
            © {new Date().getFullYear()} ResumeRoast. {isHinglish ? 'Haq se banaya gaya.' : 'All rights reserved.'}
          </div>
        </div>

      </div>
    </footer>
  )
}
