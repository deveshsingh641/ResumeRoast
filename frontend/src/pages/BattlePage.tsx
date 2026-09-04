import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { normalizeLang } from '@/i18n/detector'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import axios from 'axios'
import ScoreStamp from '@/components/ScoreStamp'
import PaperMockup from '@/components/PaperMockup'
import { IssueList } from '@/components/IssueCard'
import BattleShareCard from '@/components/BattleShareCard'
import DeskClutter from '@/components/DeskClutter'

export default function BattlePage() {
  const { id } = useParams<{ id: string }>()
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'

  const [file1, setFile1] = useState<File | null>(null)
  const [file2, setFile2] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [battleData, setBattleData] = useState<any | null>(null)

  // Fetch existing battle if id provided
  useEffect(() => {
    if (!id) return
    const fetchBattle = async () => {
      try {
        setLoading(true)
        setError(null)
        const { data } = await axios.get(`/api/battle/${id}`)
        setBattleData(data)
      } catch (err: any) {
        setError(isHinglish ? 'This battle could not be found or has expired.' : 'This battle could not be found or has expired.')
      } finally {
        setLoading(false)
      }
    }
    fetchBattle()
  }, [id, isHinglish])

  const handleStartBattle = async () => {
    if (!file1 || !file2) {
      setError(isHinglish ? 'Please select both resumes before starting the battle.' : 'Please select both resumes before starting the battle.')
      return
    }

    if (file1.size === 0 || file2.size === 0) {
      setError(isHinglish ? 'One of your files is empty (0 bytes). Please upload complete resume documents.' : 'One of your files is empty (0 bytes). Please upload complete resume documents.')
      return
    }

    if (file1.size > 5 * 1024 * 1024 || file2.size > 5 * 1024 * 1024) {
      setError(isHinglish ? 'Maximum supported size is 5MB per resume file.' : 'Maximum supported size is 5MB per resume file.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      const formData = new FormData()
      formData.append('fighter1', file1)
      formData.append('fighter2', file2)

      const { data } = await axios.post('/api/battle', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setBattleData(data)
      window.history.pushState({}, '', `/battle/${data.id}`)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      let msg = isHinglish ? 'Failed to start battle. Please check your files.' : 'Failed to start battle. Please check your files.'
      if (typeof detail === 'object' && detail?.message) {
        msg = detail.message
      } else if (typeof detail === 'string') {
        msg = detail
      } else if (err?.message) {
        msg = err.message
      }
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen pb-24 desk-cursor relative overflow-hidden">
      {/* Tactile Desk Clutter */}
      <DeskClutter stickyText={isHinglish ? 'winner gets the referral 🥊' : 'winner gets the referral 🥊'} stickyRotation={3} />

      {/* Header */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-8 relative z-10">
        <div className="max-w-[1100px] mx-auto flex items-center justify-between">
          <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
            RESUME<span className="text-stamp">ROAST</span> <span className="text-ember font-mono text-xs ml-1">// BATTLE</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/wall" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              {isHinglish ? 'Wall of Fame/Shame →' : 'Wall of Fame/Shame →'}
            </Link>
            <Link to="/roast" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
              {isHinglish ? 'Single Roast →' : 'Single Roast →'}
            </Link>
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      <div className="max-w-[1100px] mx-auto px-4 space-y-12 text-center">
        {/* Title */}
        <div>
          <p className="section-label mb-2">
            {isHinglish ? '1-ON-1 RESUME KA DANGAL' : '1-ON-1 RESUME FACE-OFF'}
          </p>
          <h1 className="font-display text-3xl sm:text-5xl text-paper tracking-tight">
            Resume <span className="text-stamp">Roast Battle</span>
          </h1>
          <p className="font-mono text-xs text-tan-dim mt-2 max-w-[600px] mx-auto">
            {isHinglish
              ? 'Do resume desk pe daal. AI referee karega dangal aur batayega kiska kachra kam hai.'
              : 'Drop two resumes on the desk. The AI referee crowns the winner and roasts both.'}
          </p>
        </div>

        {/* Upload Slots (if no battle data yet) */}
        {!battleData && (
          <div className="max-w-[840px] mx-auto space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Fighter 1 Slot */}
              <div className="border border-dashed border-white/20 hover:border-amber-400/50 rounded-lg p-6 bg-white/[0.02] text-left transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-xs text-amber-400 font-bold uppercase tracking-wider">
                    🥊 FIGHTER 1 (TERA RESUME)
                  </span>
                  {file1 && <span className="font-mono text-xs text-emerald-400">✓ Ready</span>}
                </div>
                <input
                  type="file"
                  id="fighter1-input"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setFile1(e.target.files[0])
                  }}
                />
                <label
                  htmlFor="fighter1-input"
                  className="cursor-pointer block border border-white/10 hover:border-white/30 rounded p-6 text-center bg-black/30"
                >
                  <p className="text-2xl mb-2">📄</p>
                  <p className="font-mono text-xs text-paper font-bold truncate">
                    {file1 ? file1.name : 'Pehla Resume Chuno (PDF/DOCX)'}
                  </p>
                  <p className="font-mono text-[10px] text-tan-dim mt-1">File choose karne ke liye click karo</p>
                </label>
              </div>

              {/* Fighter 2 Slot */}
              <div className="border border-dashed border-white/20 hover:border-ember/50 rounded-lg p-6 bg-white/[0.02] text-left transition-colors">
                <div className="flex items-center justify-between mb-4">
                  <span className="font-mono text-xs text-ember font-bold uppercase tracking-wider">
                    🥊 FIGHTER 2 (DOST YA RIVAL KA RESUME)
                  </span>
                  {file2 && <span className="font-mono text-xs text-emerald-400">✓ Ready</span>}
                </div>
                <input
                  type="file"
                  id="fighter2-input"
                  accept=".pdf,.docx"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setFile2(e.target.files[0])
                  }}
                />
                <label
                  htmlFor="fighter2-input"
                  className="cursor-pointer block border border-white/10 hover:border-white/30 rounded p-6 text-center bg-black/30"
                >
                  <p className="text-2xl mb-2">📄</p>
                  <p className="font-mono text-xs text-paper font-bold truncate">
                    {file2 ? file2.name : 'Doosra Resume Chuno (PDF/DOCX)'}
                  </p>
                  <p className="font-mono text-[10px] text-tan-dim mt-1">File choose karne ke liye click karo</p>
                </label>
              </div>
            </div>

            {error && (
              <p className="font-mono text-xs text-ember bg-ember/10 border border-ember/30 rounded p-3">
                {error}
              </p>
            )}

            <button
              type="button"
              onClick={handleStartBattle}
              disabled={loading || !file1 || !file2}
              className="btn-primary w-full sm:w-auto sm:px-12 py-3 text-sm justify-center shadow-lg"
            >
              {loading ? 'Dono fighters ko inspect kar rahe hain… 🥊' : '⚔️ DANGAL SHURU KARO'}
            </button>
          </div>
        )}

        {/* ── Battle Results Display ── */}
        {battleData && (
          <div className="space-y-12 animate-fade-in">
            {/* Center Official Verdict Banner */}
            <div className="bg-gradient-to-r from-bg via-[#211614] to-bg border border-stamp/40 rounded-lg p-6 sm:p-8 max-w-[860px] mx-auto shadow-2xl">
              <div className="flex items-center justify-center gap-2 mb-2">
                <span className="font-mono text-xs text-amber-400 uppercase tracking-widest">
                  REFEREE VERDICT // {battleData.margin} {battleData.winner.toUpperCase()}
                </span>
              </div>
              <h2 className="font-display text-2xl sm:text-4xl text-paper mb-4 leading-snug">
                "{battleData.verdict}"
              </h2>

              {/* Best callouts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left pt-4 border-t border-white/[0.08]">
                <div className="bg-black/30 p-3 rounded border border-white/5">
                  <p className="font-mono text-[10px] text-amber-400 uppercase font-bold">Fighter 1 Note:</p>
                  <p className="font-mono text-xs text-tan-light mt-1">"{battleData.fighter_1_best_line}"</p>
                </div>
                <div className="bg-black/30 p-3 rounded border border-white/5">
                  <p className="font-mono text-[10px] text-ember uppercase font-bold">Fighter 2 Note:</p>
                  <p className="font-mono text-xs text-tan-light mt-1">"{battleData.fighter_2_best_line}"</p>
                </div>
              </div>
            </div>

            {/* Side-by-Side Fighters */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 text-left max-w-[1100px] mx-auto">
              {/* Fighter 1 Card */}
              <div
                className={`relative border rounded-lg p-6 bg-bg transition-all ${
                  battleData.winner === 'fighter_1'
                    ? 'border-amber-400/60 shadow-[0_0_30px_rgba(255,185,60,0.15)]'
                    : 'border-white/[0.08]'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="font-mono text-xs text-amber-400 font-bold uppercase">
                      Fighter 1 {battleData.winner === 'fighter_1' && '👑 WINNER'}
                    </span>
                    <h3 className="font-display text-lg text-paper truncate max-w-[220px]">
                      {battleData.fighter_1.name}
                    </h3>
                  </div>
                  <ScoreStamp
                    score={battleData.fighter_1.overall_score}
                    band={battleData.fighter_1.band}
                    size="sm"
                    animate={false}
                  />
                </div>

                <div className="mb-4">
                  <p className="font-mono text-xs text-tan italic">"{battleData.fighter_1.one_line_verdict}"</p>
                </div>

                <IssueList
                  issues={battleData.fighter_1.issues || []}
                  totalIssues={battleData.fighter_1.total_issues || 3}
                  isTruncated={false}
                />
              </div>

              {/* Fighter 2 Card */}
              <div
                className={`relative border rounded-lg p-6 bg-bg transition-all ${
                  battleData.winner === 'fighter_2'
                    ? 'border-ember/60 shadow-[0_0_30px_rgba(232,66,45,0.15)]'
                    : 'border-white/[0.08]'
                }`}
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <span className="font-mono text-xs text-ember font-bold uppercase">
                      Fighter 2 {battleData.winner === 'fighter_2' && '👑 WINNER'}
                    </span>
                    <h3 className="font-display text-lg text-paper truncate max-w-[220px]">
                      {battleData.fighter_2.name}
                    </h3>
                  </div>
                  <ScoreStamp
                    score={battleData.fighter_2.overall_score}
                    band={battleData.fighter_2.band}
                    size="sm"
                    animate={false}
                  />
                </div>

                <div className="mb-4">
                  <p className="font-mono text-xs text-tan italic">"{battleData.fighter_2.one_line_verdict}"</p>
                </div>

                <IssueList
                  issues={battleData.fighter_2.issues || []}
                  totalIssues={battleData.fighter_2.total_issues || 3}
                  isTruncated={false}
                />
              </div>
            </div>

            {/* Battle Share Card Generator */}
            <div className="pt-6">
              <p className="section-label mb-2">SHARE THE VS DAMAGE</p>
              <BattleShareCard battle={battleData} />
            </div>

            {/* Battle again CTA */}
            <div className="pt-8 flex justify-center gap-4">
              <button
                type="button"
                onClick={() => {
                  setBattleData(null)
                  setFile1(null)
                  setFile2(null)
                  window.history.pushState({}, '', '/battle')
                }}
                className="btn-ghost"
              >
                Start another battle 🥊
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
