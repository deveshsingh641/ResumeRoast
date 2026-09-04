import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import axios from 'axios'
import ScoreStamp from '@/components/ScoreStamp'
import DeskClutter from '@/components/DeskClutter'
import type { ScoreBand } from '@/store/useAppStore'

interface WallEntry {
  id: string
  type: 'shame' | 'fame'
  score: number
  band: ScoreBand
  one_line_verdict: string
  top_roast_lines: string[]
  created_at: string
}

export default function WallPage() {
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'

  const [activeTab, setActiveTab] = useState<'shame' | 'fame'>('shame')
  const [sortBy, setSortBy] = useState<'recent' | 'score'>('recent')
  const [entries, setEntries] = useState<WallEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [flaggedIds, setFlaggedIds] = useState<Set<string>>(new Set())

  const fetchWall = async (type: 'shame' | 'fame', sort: 'recent' | 'score') => {
    try {
      setLoading(true)
      const { data } = await axios.get(`/api/wall?type=${type}&sort=${sort}&limit=24`)
      setEntries(data.items || [])
    } catch (err) {
      console.warn('Failed to load wall feed:', err)
      // Fallback demo entries
      setEntries(
        type === 'shame'
          ? [
              {
                id: 'shame-1',
                type: 'shame',
                score: 28,
                band: 'weak',
                one_line_verdict: isHinglish
                  ? 'Bhai resume hai ya suspense novel? 🕵️'
                  : 'Is this a resume or an unsolved mystery novel? 🕵️',
                top_roast_lines: isHinglish
                  ? [
                      '"Responsible for" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.',
                      'Declaration 2005 ka kyu daal rakha hai? Modern resume mein iski zaroorat nahi.',
                    ]
                  : [
                      'Stop using "Responsible for" 😩 Recruiters want verifiable metrics, not generic bedtime stories.',
                      'A declaration statement from 2005? Modern tech resumes do not include legal disclaimers.',
                    ],
                created_at: new Date().toISOString(),
              },
              {
                id: 'shame-2',
                type: 'shame',
                score: 34,
                band: 'weak',
                one_line_verdict: isHinglish
                  ? 'Design dekh ke aankhon se aansu nikal gaye 😭'
                  : 'Looking at this template brought tears to our eyes 😭',
                top_roast_lines: isHinglish
                  ? [
                      'Arre yaar "Pythno" aur "Jacascript"? 🤡 Spellcheck skip kar diya kya?',
                      '4 page ka resume? Novel likh rahe ho kya bhai?',
                    ]
                  : [
                      'Did you really type "Pythno" and "Jacascript"? 🤡 Spellcheck has left the building.',
                      '4 pages for an entry-level resume? What are you writing, an autobiography?',
                    ],
                created_at: new Date().toISOString(),
              },
            ]
          : [
              {
                id: 'fame-1',
                type: 'fame',
                score: 88,
                band: 'strong',
                one_line_verdict: isHinglish
                  ? 'Ekdum solid profile hai boss, bas thoda polish karo 🔥'
                  : 'Genuinely solid profile, just needs minor final polish 🔥',
                top_roast_lines: isHinglish
                  ? [
                      'FastAPI aur React ka combination mast hai, metrics bhi crisp hain.',
                      'GitHub live links clean hain, ATS easily parse karega.',
                    ]
                  : [
                      'The FastAPI and React stack is well quantified with crisp business impact.',
                      'GitHub live repository links are clean and effortlessly parseable by ATS systems.',
                    ],
                created_at: new Date().toISOString(),
              },
            ]
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWall(activeTab, sortBy)
  }, [activeTab, sortBy])

  const handleFlag = async (id: string) => {
    if (flaggedIds.has(id)) return
    try {
      await axios.post(`/api/wall/${id}/flag`)
      setFlaggedIds((prev) => new Set(prev).add(id))
    } catch {
      setFlaggedIds((prev) => new Set(prev).add(id))
    }
  }

  return (
    <main className="min-h-screen pb-24 desk-cursor relative overflow-hidden">
      {/* Tactile Desk Clutter */}
      <DeskClutter stickyText={isHinglish ? 'anonymized roasts ka dher 🔥' : 'hall of anonymous damage 🔥'} stickyRotation={-3} />

      {/* Header */}
      <header className="border-b border-white/[0.08] py-3 sm:py-4 px-3 sm:px-6 mb-6 sm:mb-8 relative z-10">
        <div className="max-w-[1100px] mx-auto flex items-center justify-between gap-2">
          <Link to="/" className="font-display text-base sm:text-lg tracking-tight text-paper select-none shrink-0">
            RESUME<span className="text-stamp">ROAST</span> <span className="text-amber-400 font-mono text-[10px] sm:text-xs ml-0.5 sm:ml-1">// WALL</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            <Link to="/battle" className="font-mono text-[11px] sm:text-xs text-tan-dim hover:text-tan transition-colors whitespace-nowrap">
              <span className="hidden sm:inline">⚔️ Battle Mode →</span>
              <span className="sm:hidden">⚔️ Battle</span>
            </Link>
            <Link to="/roast" className="font-mono text-[11px] sm:text-xs text-tan-dim hover:text-tan transition-colors whitespace-nowrap">
              <span className="hidden sm:inline">Grade Resume →</span>
              <span className="sm:hidden">Grade</span>
            </Link>
            <LanguageSwitcher compact={true} className="shrink-0" />
          </div>
        </div>
      </header>

      <div className="max-w-[1100px] mx-auto px-4 space-y-10 relative z-10">
        {/* Title */}
        <div className="text-center">
          <p className="section-label mb-2">
            {isHinglish ? 'ASLI CANDIDATES KA ANONYMOUS DAMAGE' : 'PUBLIC ANONYMOUS HALL OF DAMAGE'}
          </p>
          <h1 className="font-display text-3xl sm:text-5xl text-paper tracking-tight">
            Wall of <span className={activeTab === 'shame' ? 'text-stamp' : 'text-amber-400'}>{activeTab === 'shame' ? 'Shame' : 'Fame'}</span>
          </h1>
          <p className="font-mono text-xs text-tan-dim mt-2 max-w-[580px] mx-auto">
            {isHinglish
              ? 'Brave candidates ke asli anonymized resumes. Saare personal names aur emails pehle hi sanitize kar diye gaye hain.'
              : 'Real anonymized resumes submitted by brave candidates. All personal data, emails, and company names have been pre-sanitized.'}
          </p>
        </div>

        {/* Tab switcher & Sorting */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-white/[0.08] pb-4 max-w-[960px] mx-auto">
          {/* Tabs */}
          <div className="flex items-center gap-2 p-1 bg-white/[0.03] border border-white/[0.08] rounded-sm">
            <button
              type="button"
              onClick={() => setActiveTab('shame')}
              className={`px-4 py-2 rounded-sm text-xs font-mono font-bold transition-all ${
                activeTab === 'shame'
                  ? 'bg-stamp text-paper shadow-sm'
                  : 'text-tan-dim hover:text-tan'
              }`}
            >
              🔥 Wall of Shame (Score ≤ 50)
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('fame')}
              className={`px-4 py-2 rounded-sm text-xs font-mono font-bold transition-all ${
                activeTab === 'fame'
                  ? 'bg-amber-400 text-bg shadow-sm'
                  : 'text-tan-dim hover:text-tan'
              }`}
            >
              🏆 Wall of Fame (Score &gt; 50)
            </button>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2 font-mono text-xs text-tan-dim">
            <span>{isHinglish ? 'Kram:' : 'Sort by:'}</span>
            <button
              type="button"
              onClick={() => setSortBy('recent')}
              className={`px-2 py-1 rounded-sm transition-colors ${
                sortBy === 'recent' ? 'text-amber-400 bg-white/[0.06]' : 'hover:text-tan'
              }`}
            >
              {isHinglish ? 'Sabse Naya' : 'Most Recent'}
            </button>
            <span>/</span>
            <button
              type="button"
              onClick={() => setSortBy('score')}
              className={`px-2 py-1 rounded-sm transition-colors ${
                sortBy === 'score' ? 'text-amber-400 bg-white/[0.06]' : 'hover:text-tan'
              }`}
            >
              {activeTab === 'shame' 
                ? (isHinglish ? 'Bhaari Nuksaan' : 'Highest Damage') 
                : (isHinglish ? 'Top Score' : 'Top Score')}
            </button>
          </div>
        </div>

        {/* Conversion Loop Banner */}
        <div className="max-w-[960px] mx-auto bg-gradient-to-r from-[#17140F] via-white/[0.03] to-[#17140F] border border-white/[0.08] rounded-sm p-5 flex flex-col sm:flex-row items-center justify-between gap-4 text-left">
          <div>
            <p className="font-display text-base text-paper">
              {activeTab === 'shame'
                ? (isHinglish ? 'Lagta hai tera resume isse bhi zyada disastrous hai? 👀' : 'Think your resume is even more disastrous? 👀')
                : (isHinglish ? 'Lagta hai tu in scores ko beat kar sakta hai? 🚀' : 'Think you can beat these scores? 🚀')}
            </p>
            <p className="font-mono text-xs text-tan-dim">
              {isHinglish
                ? 'Apna resume upload kar brutal red-pen roast ke liye aur rank check kar.'
                : 'Upload your resume for a brutal red-pen roast and see where you rank.'}
            </p>
          </div>
          <Link to="/roast" className="btn-primary shrink-0 text-xs">
            {isHinglish ? 'Abhi resume roast karwayein' : 'Roast my resume now'}
          </Link>
        </div>

        {/* Weekly Spotlight Feature */}
        <section
          aria-label="Weekly Spotlight"
          className="max-w-[960px] mx-auto bg-gradient-to-br from-[#24130F] to-[#14100C] border-2 border-amber-500/40 rounded-sm p-6 text-left relative overflow-hidden shadow-2xl"
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4 border-b border-white/[0.08] pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xl">🌟</span>
              <div>
                <span className="font-mono text-[10px] text-amber-400 font-bold uppercase tracking-widest block">
                  WEEKLY SPOTLIGHT // MOST VIRAL SUBMISSION
                </span>
                <h2 className="font-display text-lg sm:text-xl text-paper">
                  {activeTab === 'shame' ? 'This Week’s Hall of Disaster Champion' : 'This Week’s Benchmark Resume'}
                </h2>
              </div>
            </div>
            <span className="font-mono text-xs px-2.5 py-1 bg-amber-400/10 border border-amber-400/30 text-amber-300 rounded-sm">
              🔥 1,420 shares this week
            </span>
          </div>

          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 bg-black/40 border border-white/10 rounded-sm p-4">
            <div className="flex-1 space-y-2">
              <p className="font-display text-base sm:text-lg text-paper">
                "{activeTab === 'shame'
                  ? 'Bhai resume hai ya suspense novel? 🕵️ 4 page ka resume dekh ke ATS behosh ho gaya.'
                  : 'FastAPI aur React ka crisp integration with real performance metrics! 🚀'}"
              </p>
              <div className="flex flex-wrap gap-2 text-[11px] font-mono text-tan-dim">
                <span className="bg-white/[0.05] px-2 py-0.5 rounded-[2px]">
                  {activeTab === 'shame' ? '❌ 14 Buzzwords' : '✅ 8 Metrics Included'}
                </span>
                <span className="bg-white/[0.05] px-2 py-0.5 rounded-[2px]">
                  {activeTab === 'shame' ? '❌ 0 Numbers' : '✅ Clean 1-Page Layout'}
                </span>
              </div>
            </div>

            <div className="shrink-0 flex items-center gap-4">
              <ScoreStamp
                score={activeTab === 'shame' ? 22 : 92}
                band={activeTab === 'shame' ? 'weak' : 'strong'}
                size="md"
                animate={false}
              />
              <Link to="/roast" className="btn-primary !text-xs !py-2 !px-3">
                Beat this score →
              </Link>
            </div>
          </div>
        </section>

        {/* Grid of PaperMockup-lite Wall Cards */}
        {loading ? (
          <div className="text-center py-16 font-mono text-xs text-tan-dim">
            Loading public wall entries…
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-white/10 rounded-sm max-w-[640px] mx-auto">
            <p className="text-3xl mb-2">{activeTab === 'shame' ? '👻' : '🏅'}</p>
            <p className="font-mono text-xs text-paper">No entries on this wall yet.</p>
            <p className="font-mono text-[10px] text-tan-dim mt-1">Be the first to roast and post your resume!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-[1100px] mx-auto text-left">
            {entries.map((entry, idx) => {
              // Slight deterministic rotation per card (-1.2deg to 1.2deg)
              const cardRotation = ((idx % 5) - 2) * 0.6
              return (
                <div
                  key={entry.id}
                  className="paper-mockup-card bg-paper text-ink rounded-sm p-5 flex flex-col justify-between transition-all relative shadow-paper border border-black/10 group hover:-translate-y-1"
                  style={{
                    transform: `rotate(${cardRotation}deg)`,
                    ['--paper-rotate' as string]: `${cardRotation}deg`,
                  }}
                >
                  {/* Top: ScoreStamp & Type */}
                  <div>
                    <div className="flex items-center justify-between mb-3 border-b border-black/10 pb-2">
                      <span className="font-mono text-[10px] text-ink/60 uppercase font-semibold">
                        {entry.type === 'shame' ? '🔥 DISASTER ENTRY' : '⭐ HALL OF FAME'}
                      </span>
                      <ScoreStamp
                        score={entry.score}
                        band={entry.band}
                        size="sm"
                        animate={false}
                      />
                    </div>

                    {/* Verdict */}
                    <h3 className="font-display text-base text-ink leading-snug mb-3">
                      "{entry.one_line_verdict}"
                    </h3>

                    {/* Redacted Roast Snippets */}
                    <div className="space-y-2 mb-4">
                      {entry.top_roast_lines?.map((line, lIdx) => (
                        <div key={lIdx} className="bg-black/[0.04] border-l-2 border-stamp rounded-[1px] p-2">
                          <p className="font-mono text-xs text-ink/85 leading-relaxed">
                            {line}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Bottom: Flag / Report with subtle hover appearance */}
                  <div className="pt-2.5 border-t border-black/10 flex items-center justify-between text-[10px] font-mono text-ink/60">
                    <span>ANONYMOUS CANDIDATE</span>
                    <button
                      type="button"
                      onClick={() => handleFlag(entry.id)}
                      disabled={flaggedIds.has(entry.id)}
                      className="opacity-60 hover:opacity-100 hover:text-stamp transition-opacity flex items-center gap-1"
                      title="Report this entry"
                    >
                      {flaggedIds.has(entry.id) ? '✓ Reported' : '🚩 Flag'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </main>
  )
}
