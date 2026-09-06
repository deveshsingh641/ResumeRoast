import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { usePageTitle } from '@/utils/usePageTitle'

interface MetricsSummary {
  total_roasts_all_time: number
  total_battles_all_time: number
  unique_visitors_today: number
  pageviews_today: number
  waitlist_signups: number
  pro_subscribers: number
  estimated_mrr_inr: number
}

interface RoastItem {
  id: string
  overall_score: number
  band: string
  one_line_verdict: string
  resume_text?: string
  created_at: string
  upload_count?: number
  first_created_at?: string
}

interface SuggestionItem {
  id: string
  text: string
  category: string
  status: string
  email?: string | null
  created_at: string
}

interface TrafficDay {
  date: string
  unique_visitors: number
  pageviews: number
}

export default function FounderDashboardPage() {
  usePageTitle('Founder Executive Desk')

  const [searchParams] = useSearchParams()
  const [adminKey, setAdminKey] = useState<string>(() => {
    return searchParams.get('key') || sessionStorage.getItem('rr_admin_key') || ''
  })
  const [inputKey, setInputKey] = useState('')
  const [authError, setAuthError] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  // Dashboard state
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null)
  const [trafficHistory, setTrafficHistory] = useState<TrafficDay[]>([])
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([])
  const [topPaths, setTopPaths] = useState<Array<{ path: string; views: number }>>([])

  // Paginated Roasts Explorer State
  const [recentRoasts, setRecentRoasts] = useState<RoastItem[]>([])
  const [totalRoastsCount, setTotalRoastsCount] = useState(0)
  const [totalUniqueCount, setTotalUniqueCount] = useState(0)
  const [totalAllCount, setTotalAllCount] = useState(0)
  const [roastsUniqueOnly, setRoastsUniqueOnly] = useState(true)
  const [roastsLimit, setRoastsLimit] = useState(25)
  const [roastsOffset, setRoastsOffset] = useState(0)
  const [roastsSearch, setRoastsSearch] = useState('')
  const [roastsBand, setRoastsBand] = useState('all')
  const [roastsLoading, setRoastsLoading] = useState(false)

  // Support Override Tool State
  const [overrideEmail, setOverrideEmail] = useState('')
  const [overrideAction, setOverrideAction] = useState<'grant_pro' | 'revoke_pro'>('grant_pro')
  const [overrideReason, setOverrideReason] = useState('')
  const [overrideMsg, setOverrideMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [overrideLoading, setOverrideLoading] = useState(false)

  // Load paginated roasts
  const loadRoasts = async (
    keyToUse: string,
    offset: number = roastsOffset,
    limit: number = roastsLimit,
    search: string = roastsSearch,
    band: string = roastsBand,
    uniqueOnly: boolean = roastsUniqueOnly
  ) => {
    setRoastsLoading(true)
    try {
      const headers = { 'X-Admin-Key': keyToUse }
      const params = new URLSearchParams()
      params.set('limit', String(limit))
      params.set('offset', String(offset))
      params.set('unique', String(uniqueOnly))
      if (search.trim()) params.set('search', search.trim())
      if (band && band !== 'all') params.set('band', band)

      const { data } = await axios.get(`/api/admin/roasts?${params.toString()}`, { headers })
      if (data && data.ok) {
        setRecentRoasts(data.roasts || [])
        setTotalRoastsCount(data.total || 0)
        setTotalUniqueCount(data.total_unique || data.total || 0)
        setTotalAllCount(data.total_all || 0)
      }
    } catch (err) {
      console.warn('Failed to load roasts:', err)
    } finally {
      setRoastsLoading(false)
    }
  }

  // Validate admin key and load dashboard
  const fetchDashboardData = async (keyToUse: string) => {
    setLoading(true)
    setAuthError('')
    try {
      const headers = { 'X-Admin-Key': keyToUse }

      // 1. Fetch metrics
      const { data: metricsData } = await axios.get('/api/admin/metrics', { headers })
      if (metricsData && metricsData.ok) {
        setMetrics(metricsData.summary)
        setTrafficHistory(metricsData.traffic_7d || [])
      }

      // 2. Fetch paginated roasts
      await loadRoasts(keyToUse, 0, roastsLimit, roastsSearch, roastsBand)
      setRoastsOffset(0)

      // 3. Fetch user suggestions
      const { data: suggData } = await axios.get('/api/admin/suggestions?limit=100', { headers })
      if (suggData && suggData.ok) {
        setSuggestions(suggData.suggestions || [])
      }

      // 4. Fetch path stats
      try {
        const { data: statsData } = await axios.get('/api/stats', { headers })
        if (statsData && statsData.top_paths_today) {
          setTopPaths(statsData.top_paths_today)
        }
      } catch {
        // non-blocking
      }

      // Success: store strictly in temporary browser session
      setIsAuthenticated(true)
      sessionStorage.setItem('rr_admin_key', keyToUse)
    } catch (err: any) {
      console.warn('Founder auth check:', err.response?.status)
      setIsAuthenticated(false)
      sessionStorage.removeItem('rr_admin_key')

      if (err.response?.status === 429) {
        setAuthError(
          err.response?.data?.detail ||
            'Security Lockout: Too many failed founder authentication attempts. Try again in 15 minutes.'
        )
      } else if (err.response?.status === 401) {
        setAuthError('Invalid founder secret key. Access denied.')
      } else {
        setAuthError('Failed to connect to backend server. Please make sure backend is running.')
      }
    } finally {
      setLoading(false)
    }
  }

  // Attempt auto-login if key is already present
  useEffect(() => {
    if (adminKey) {
      fetchDashboardData(adminKey)
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    const clean = inputKey.trim()
    if (!clean) return
    setAdminKey(clean)
    fetchDashboardData(clean)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setAdminKey('')
    setInputKey('')
    sessionStorage.removeItem('rr_admin_key')
  }

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!overrideEmail.trim()) return
    setOverrideLoading(true)
    setOverrideMsg(null)
    try {
      const { data } = await axios.post(
        '/api/admin/user/override-pro',
        {
          email: overrideEmail.trim(),
          action: overrideAction,
          reason: overrideReason.trim() || 'Founder manual override',
        },
        { headers: { 'X-Admin-Key': adminKey } }
      )
      if (data && data.ok) {
        setOverrideMsg({ text: `✓ ${data.message}`, ok: true })
        setOverrideEmail('')
        setOverrideReason('')
        // Refresh metrics
        fetchDashboardData(adminKey)
      } else {
        throw new Error(data.detail || 'Failed to update')
      }
    } catch (err: any) {
      setOverrideMsg({
        text: `✗ ${err.response?.data?.detail || err.message || 'Error occurred'}`,
        ok: false,
      })
    } finally {
      setOverrideLoading(false)
    }
  }

  const handleUpdateSuggestionStatus = async (id: string, newStatus: string) => {
    try {
      await axios.patch(
        `/api/admin/suggestions/${id}`,
        { status: newStatus },
        { headers: { 'X-Admin-Key': adminKey } }
      )
      setSuggestions((prev) =>
        prev.map((s) => (s.id === id ? { ...s, status: newStatus } : s))
      )
    } catch (err) {
      console.error('Failed to update suggestion status:', err)
    }
  }

  // 1. Render Login Screen if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#0D0A08] text-paper flex items-center justify-center p-4">
        <div className="w-full max-w-sm bg-[#1A1613] border border-white/10 rounded-xl p-7 sm:p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 text-2xl mb-3">
              🔒
            </div>
            <h1 className="text-xl font-black tracking-tight text-white uppercase font-display">
              Founder Access Only
            </h1>
            <p className="text-xs text-tan-dim font-mono mt-1.5 leading-relaxed">
              Enter secret founder key to access live metrics, visitor stats & feedback.
            </p>
          </div>

          {authError && (
            <div className="p-3 mb-4 rounded bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono">
              ⚠️ {authError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-[10px] font-mono uppercase text-tan-dim mb-1.5 tracking-wider font-bold">
                Secret Founder Key
              </label>
              <input
                type="password"
                required
                autoFocus
                value={inputKey}
                onChange={(e) => setInputKey(e.target.value)}
                placeholder="Enter confidential founder key..."
                className="w-full bg-black/60 border border-white/20 rounded-lg px-3.5 py-2.5 text-sm font-mono text-white placeholder:text-stone-600 focus:outline-none focus:border-amber-400 transition"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 rounded-lg bg-[#E8422D] hover:bg-[#D43723] text-white font-mono font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-red-900/30 cursor-pointer disabled:opacity-50"
            >
              {loading ? 'Verifying...' : 'Unlock Dashboard ⚡'}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-white/[0.08] text-center">
            <Link to="/" className="text-xs font-mono text-tan-dim hover:text-amber-400 transition">
              ← Return to Public Homepage
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // 2. Render Full Executive Dashboard
  return (
    <div className="min-h-screen bg-[#120F0D] text-paper font-body p-4 sm:p-8 md:p-10 max-w-5xl mx-auto">
      {/* ── Top Header ── */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-8 border-b border-white/10 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
              🔒 Founder Executive Desk
            </span>
            <span className="text-xs text-tan-dim font-mono">Devesh Singh (Creator)</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight mt-1 text-white font-display">
            RESUME<span className="text-stamp">ROAST</span> FOUNDER METRICS
          </h1>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => fetchDashboardData(adminKey)}
            disabled={loading}
            className="px-3 py-1.5 rounded text-xs font-mono font-bold bg-white/10 hover:bg-white/20 text-stone-200 border border-white/10 transition cursor-pointer"
          >
            {loading ? 'Refreshing...' : '↻ Refresh Data'}
          </button>
          <button
            type="button"
            onClick={handleLogout}
            className="px-3 py-1.5 rounded text-xs font-mono font-bold bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30 transition cursor-pointer"
          >
            🔒 Logout
          </button>
        </div>
      </header>

      {/* ── Section 1: Top Hero Metric Cards (100% Real Live Counters) ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        {/* Visitors Today */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Unique Visitors Today</div>
          <div className="text-3xl font-extrabold text-white mt-1 font-display">
            {metrics?.unique_visitors_today ?? 0}
          </div>
          <div className="text-[11px] text-emerald-400 font-mono mt-2 flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            Real deduplicated users
          </div>
        </div>

        {/* Pageviews Today */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Total Page Views Today</div>
          <div className="text-3xl font-extrabold text-amber-400 mt-1 font-display">
            {metrics?.pageviews_today ?? 0}
          </div>
          <div className="text-[11px] text-tan-dim font-mono mt-2">First-party hit beacon</div>
        </div>

        {/* Roasts in DB */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Total Roasts Created</div>
          <div className="text-3xl font-extrabold text-stamp mt-1 font-display">
            {metrics?.total_roasts_all_time ?? 0}
          </div>
          <div className="text-[11px] text-tan-dim font-mono mt-2">Stored in Supabase DB</div>
        </div>

        {/* Live User Suggestions */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Live User Suggestions</div>
          <div className="text-3xl font-extrabold text-sky-400 mt-1 font-display">
            {suggestions.length}
          </div>
          <div className="text-[11px] text-tan-dim font-mono mt-2">Ideas & feedback received</div>
        </div>
      </div>

      {/* ── Section 2: Infrastructure & Commercial Readiness ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* VIP Pro Waitlist */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">VIP Pro Waitlist</div>
          <div className="text-3xl font-extrabold text-amber-300 mt-1 font-display">
            {metrics?.waitlist_signups ?? 0}
          </div>
          <div className="text-[11px] text-amber-400 font-mono mt-2">● Warmed launch leads</div>
        </div>

        {/* AI Provider & Cost */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">AI Provider & Cost</div>
          <div className="text-base font-bold text-sky-400 mt-1 font-mono">Gemini 2.5 Flash</div>
          <div className="text-[11px] text-emerald-400 font-mono mt-2">Free API Tier ($0.00 spend)</div>
        </div>

        {/* Database Status */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Database Status</div>
          <div className="text-base font-bold text-emerald-400 mt-1 font-mono flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
            Supabase Active
          </div>
          <div className="text-[11px] text-tan-dim font-mono mt-2 truncate">aws-0-ap-northeast-1</div>
        </div>

        {/* Pro Plan Commercial Status */}
        <div className="bg-[#1A1613] p-5 rounded-lg border border-white/10">
          <div className="text-[11px] font-mono text-tan-dim uppercase">Pro Commercial Tier</div>
          <div className="text-base font-bold text-amber-400 mt-1 font-mono">Launching Soon</div>
          <div className="text-[11px] text-tan-dim font-mono mt-2">Razorpay KYC in review</div>
        </div>
      </div>

      {/* ── Section 3: Customer Support Pro Override Panel ── */}
      <div className="mb-8 bg-[#1A1613] rounded-lg border border-white/10 p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-white/10">
          <div>
            <h2 className="font-bold text-sm tracking-wide text-white font-mono uppercase">
              🛠️ Customer Support Instant Pro Override
            </h2>
            <p className="text-xs text-tan-dim font-mono mt-0.5">
              Manually grant or revoke Pro pass for a user email (bypasses payment delays)
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
            Active Support Tool
          </span>
        </div>

        <form onSubmit={handleOverrideSubmit} className="flex flex-col sm:flex-row gap-3">
          <input
            type="email"
            required
            value={overrideEmail}
            onChange={(e) => setOverrideEmail(e.target.value)}
            placeholder="customer@example.com"
            className="flex-1 bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-amber-400"
          />
          <select
            value={overrideAction}
            onChange={(e) => setOverrideAction(e.target.value as any)}
            className="bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-stone-300 focus:outline-none"
          >
            <option value="grant_pro">Grant Pro (₹99 / Active)</option>
            <option value="revoke_pro">Revoke Pro (Free Tier)</option>
          </select>
          <input
            type="text"
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            placeholder="Reason (e.g. UPI ref #1234)"
            className="sm:w-48 bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-stone-300 focus:outline-none"
          />
          <button
            type="submit"
            disabled={overrideLoading}
            className="px-4 py-2 rounded text-xs font-mono font-bold bg-amber-500 hover:bg-amber-400 text-stone-950 transition shrink-0 cursor-pointer disabled:opacity-50"
          >
            {overrideLoading ? 'Processing...' : 'Execute Override ⚡'}
          </button>
        </form>

        {overrideMsg && (
          <div
            className={`mt-3 text-xs font-mono p-2.5 rounded border ${
              overrideMsg.ok
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-red-500/10 text-red-400 border-red-500/30'
            }`}
          >
            {overrideMsg.text}
          </div>
        )}
      </div>

      {/* ── Section 4: Live Suggestions Box ── */}
      <div className="mb-8 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/10 flex justify-between items-center">
          <div>
            <h2 className="font-bold text-sm tracking-wide text-white font-mono uppercase">
              💡 Suggestion Box Submissions ({suggestions.length})
            </h2>
            <p className="text-xs text-tan-dim font-mono mt-0.5">
              Ideas, feedback and bug reports submitted through the public modal
            </p>
          </div>
          <span className="text-xs font-mono text-sky-400 bg-sky-400/10 px-2 py-1 rounded border border-sky-400/20">
            Live Database Sync
          </span>
        </div>

        <div className="p-4 space-y-3 max-h-[460px] overflow-y-auto">
          {suggestions.length === 0 ? (
            <div className="py-6 text-center text-xs text-tan-dim font-mono">
              No user suggestions submitted yet.
            </div>
          ) : (
            suggestions.map((s) => {
              const statusColor =
                s.status === 'new'
                  ? '#38BDF8'
                  : s.status === 'reviewed'
                  ? '#FBBF24'
                  : s.status === 'done' || s.status === 'planned'
                  ? '#10B981'
                  : '#94A3B8'

              return (
                <div
                  key={s.id}
                  className="bg-[#14110E] p-4 rounded border border-white/[0.06] text-left hover:border-white/15 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 text-stone-300 uppercase">
                        {s.category}
                      </span>
                      <span
                        className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase"
                        style={{
                          color: statusColor,
                          backgroundColor: `${statusColor}22`,
                          border: `1px solid ${statusColor}44`,
                        }}
                      >
                        {s.status}
                      </span>
                      <span className="text-[11px] font-mono text-tan-dim">
                        {s.created_at?.slice(0, 19).replace('T', ' ')} UTC
                        {s.email ? (
                          <>
                            {' · '}
                            <span className="text-amber-400 font-bold">{s.email}</span>
                          </>
                        ) : (
                          ' · Anonymous'
                        )}
                      </span>
                    </div>

                    {/* Quick status triage dropdown */}
                    <select
                      value={s.status}
                      onChange={(e) => handleUpdateSuggestionStatus(s.id, e.target.value)}
                      className="bg-black/60 border border-white/20 rounded px-2 py-1 text-[11px] font-mono text-stone-300 focus:outline-none"
                    >
                      <option value="new">Mark New</option>
                      <option value="reviewed">Mark Reviewed</option>
                      <option value="planned">Mark Planned</option>
                      <option value="done">Mark Done</option>
                      <option value="not-planned">Not Planned</option>
                    </select>
                  </div>

                  <p className="text-xs font-mono text-stone-200 whitespace-pre-wrap leading-relaxed">
                    "{s.text}"
                  </p>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* ── Section 5: Uploaded Resumes Explorer with Deduplication & Full Pagination ── */}
      <div className="mb-8 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
        <div className="px-5 py-4 border-b border-white/10 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
          <div>
            <h2 className="font-bold text-sm tracking-wide text-white font-mono uppercase flex items-center gap-2">
              <span>📄 Uploaded Resumes Explorer</span>
              <span className="text-xs px-2.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                {roastsUniqueOnly ? `${totalUniqueCount} Unique Resumes` : `${totalAllCount} Total Uploads`}
              </span>
            </h2>
            <p className="text-xs text-tan-dim font-mono mt-0.5">
              Candidate resumes submitted for roasting · {roastsUniqueOnly ? 'Deduplicated (1 display per unique candidate resume)' : 'Raw upload log (all attempts)'}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* View Mode Toggle: Unique vs All */}
            <div className="inline-flex rounded-md p-0.5 bg-black/60 border border-white/15 text-xs font-mono">
              <button
                type="button"
                onClick={() => {
                  setRoastsUniqueOnly(true)
                  setRoastsOffset(0)
                  loadRoasts(adminKey, 0, roastsLimit, roastsSearch, roastsBand, true)
                }}
                className={`px-3 py-1 rounded transition cursor-pointer ${
                  roastsUniqueOnly
                    ? 'bg-amber-500 text-black font-bold shadow-sm'
                    : 'text-stone-400 hover:text-white'
                }`}
                title="Group multiple uploads of the same resume so each unique candidate displays only once"
              >
                ✨ Unique ({totalUniqueCount})
              </button>
              <button
                type="button"
                onClick={() => {
                  setRoastsUniqueOnly(false)
                  setRoastsOffset(0)
                  loadRoasts(adminKey, 0, roastsLimit, roastsSearch, roastsBand, false)
                }}
                className={`px-3 py-1 rounded transition cursor-pointer ${
                  !roastsUniqueOnly
                    ? 'bg-amber-500 text-black font-bold shadow-sm'
                    : 'text-stone-400 hover:text-white'
                }`}
                title="View every single upload attempt including repeat uploads"
              >
                📋 All Uploads ({totalAllCount})
              </button>
            </div>

            <span className="text-xs font-mono text-amber-400 bg-amber-400/10 px-2.5 py-1 rounded border border-amber-400/20 shrink-0">
              Live Supabase Sync
            </span>
          </div>
        </div>

        {/* Filter & Search Toolbar */}
        <div className="p-4 bg-white/[0.02] border-b border-white/[0.08] flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="flex-1 min-w-[220px]">
            <input
              type="text"
              value={roastsSearch}
              onChange={(e) => {
                const val = e.target.value
                setRoastsSearch(val)
                setRoastsOffset(0)
                loadRoasts(adminKey, 0, roastsLimit, val, roastsBand, roastsUniqueOnly)
              }}
              placeholder="🔍 Search candidate skills, text, or verdicts..."
              className="w-full bg-black/50 border border-white/20 rounded px-3 py-1.5 text-xs font-mono text-white placeholder:text-stone-600 focus:outline-none focus:border-amber-400"
            />
          </div>

          {/* Band Filter */}
          <select
            value={roastsBand}
            onChange={(e) => {
              const val = e.target.value
              setRoastsBand(val)
              setRoastsOffset(0)
              loadRoasts(adminKey, 0, roastsLimit, roastsSearch, val, roastsUniqueOnly)
            }}
            className="bg-black/50 border border-white/20 rounded px-3 py-1.5 text-xs font-mono text-stone-300 focus:outline-none"
          >
            <option value="all">All Score Bands</option>
            <option value="weak">Critical / Weak (≤ 40)</option>
            <option value="average">Needs Polish (41 - 70)</option>
            <option value="good">Interview Ready (71+)</option>
          </select>

          {/* Page Size Selector */}
          <select
            value={roastsLimit}
            onChange={(e) => {
              const val = Number(e.target.value)
              setRoastsLimit(val)
              setRoastsOffset(0)
              loadRoasts(adminKey, 0, val, roastsSearch, roastsBand, roastsUniqueOnly)
            }}
            className="bg-black/50 border border-white/20 rounded px-3 py-1.5 text-xs font-mono text-stone-300 focus:outline-none"
          >
            <option value={12}>12 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
        </div>

        {/* Resumes List */}
        <div className="p-4 space-y-4 max-h-[560px] overflow-y-auto">
          {roastsLoading ? (
            <div className="py-8 text-center text-xs text-tan-dim font-mono animate-pulse">
              Loading resumes from Supabase...
            </div>
          ) : recentRoasts.length === 0 ? (
            <div className="py-8 text-center text-xs text-tan-dim font-mono">
              {roastsSearch ? 'No resumes matching your search filter.' : 'No candidate resumes found.'}
            </div>
          ) : (
            recentRoasts.map((r) => {
              const score = r.overall_score || 0
              const scoreColor = score <= 40 ? '#E8422D' : score <= 70 ? '#FFB93C' : '#10B981'
              const resText = r.resume_text || 'No text content preserved.'
              const uploadCount = r.upload_count || 1
              const hasMultiple = uploadCount > 1

              return (
                <div
                  key={r.id}
                  className="bg-[#14110E] p-4 rounded border border-white/[0.06] text-left hover:border-white/15 transition-colors"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className="px-2 py-0.5 rounded text-xs font-mono font-bold"
                        style={{
                          color: scoreColor,
                          backgroundColor: `${scoreColor}22`,
                          border: `1px solid ${scoreColor}55`,
                        }}
                      >
                        {score}/100 · {(r.band || 'weak').toUpperCase()}
                      </span>

                      {/* Repeat Upload Badge */}
                      {hasMultiple ? (
                        <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                          Uploaded {uploadCount}x
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.5 rounded text-[11px] font-mono bg-white/5 text-stone-400 border border-white/10">
                          1st upload
                        </span>
                      )}

                      <span className="text-xs font-mono text-tan-dim">
                        {r.created_at?.slice(0, 19).replace('T', ' ')} UTC
                        {hasMultiple && r.first_created_at && r.first_created_at !== r.created_at && (
                          <span className="text-stone-500 ml-1.5">
                            (First: {r.first_created_at.slice(0, 10)})
                          </span>
                        )}
                      </span>
                    </div>

                    <Link
                      to={`/roast/${r.id}`}
                      target="_blank"
                      className="text-xs font-mono text-amber-400 hover:underline"
                    >
                      Open Public Roast ↗
                    </Link>
                  </div>

                  <p className="font-bold text-sm text-stone-200 mb-2">"{r.one_line_verdict}"</p>

                  <details className="text-xs font-mono text-tan-dim bg-black/40 p-2.5 rounded border border-white/5 cursor-pointer">
                    <summary className="hover:text-amber-300 select-none">
                      📄 View Extracted Resume Text ({resText.length} chars)
                    </summary>
                    <pre className="mt-2 text-stone-300 whitespace-pre-wrap font-mono text-[11px] max-h-64 overflow-y-auto leading-relaxed p-2 bg-black/60 rounded border border-white/5">
                      {resText}
                    </pre>
                  </details>
                </div>
              )
            })
          )}
        </div>

        {/* Pagination Controls Footer */}
        {totalRoastsCount > 0 && (
          <div className="px-5 py-3.5 bg-white/[0.02] border-t border-white/[0.08] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-tan-dim">
            <div>
              Showing {roastsOffset + 1} - {Math.min(roastsOffset + roastsLimit, totalRoastsCount)} of{' '}
              <span className="text-white font-bold">{totalRoastsCount}</span>{' '}
              {roastsUniqueOnly ? 'unique candidate resumes' : 'total upload entries'}
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                disabled={roastsOffset === 0 || roastsLoading}
                onClick={() => {
                  const newOffset = Math.max(0, roastsOffset - roastsLimit)
                  setRoastsOffset(newOffset)
                  loadRoasts(adminKey, newOffset, roastsLimit, roastsSearch, roastsBand, roastsUniqueOnly)
                }}
                className="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-stone-200 border border-white/10 transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                ← Previous
              </button>

              <span className="px-2 font-bold text-amber-400">
                Page {Math.floor(roastsOffset / roastsLimit) + 1} /{' '}
                {Math.max(1, Math.ceil(totalRoastsCount / roastsLimit))}
              </span>

              <button
                type="button"
                disabled={roastsOffset + roastsLimit >= totalRoastsCount || roastsLoading}
                onClick={() => {
                  const newOffset = roastsOffset + roastsLimit
                  setRoastsOffset(newOffset)
                  loadRoasts(adminKey, newOffset, roastsLimit, roastsSearch, roastsBand, roastsUniqueOnly)
                }}
                className="px-3 py-1.5 rounded bg-white/5 hover:bg-white/10 text-stone-200 border border-white/10 transition disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Section 6: 7-Day Traffic & Top Pages Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* History Table */}
        <div className="lg:col-span-2 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
          <div className="px-5 py-4 border-b border-white/10 flex justify-between items-center">
            <h2 className="font-bold text-sm tracking-wide text-white font-mono uppercase">
              Past 7 Days Traffic
            </h2>
            <span className="text-xs text-tan-dim font-mono">Deduplicated per day</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-[11px] font-mono text-tan-dim uppercase bg-white/[0.02]">
                  <th className="py-2.5 px-4">Date</th>
                  <th className="py-2.5 px-4">Unique Visitors</th>
                  <th className="py-2.5 px-4">Page Views</th>
                  <th className="py-2.5 px-4">Ratio</th>
                </tr>
              </thead>
              <tbody>
                {trafficHistory.map((d) => (
                  <tr key={d.date} className="border-b border-white/[0.06] hover:bg-white/[0.02]">
                    <td className="py-2.5 px-4 font-mono text-xs text-amber-200/80">{d.date}</td>
                    <td className="py-2.5 px-4 font-mono text-sm font-bold text-white">
                      {d.unique_visitors}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-sm text-stone-300">
                      {d.pageviews}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-xs text-tan-dim">
                      {d.unique_visitors > 0
                        ? `${(d.pageviews / d.unique_visitors).toFixed(1)}x`
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Paths Today */}
        <div className="bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
          <div className="px-5 py-4 border-b border-white/10">
            <h2 className="font-bold text-sm tracking-wide text-white font-mono uppercase">
              Top Pages Today
            </h2>
          </div>
          <div className="p-2 space-y-1">
            {topPaths.length === 0 ? (
              <div className="py-4 text-center text-xs text-tan-dim font-mono">
                No navigation events recorded yet today.
              </div>
            ) : (
              topPaths.map((p) => (
                <div
                  key={p.path}
                  className="flex justify-between items-center py-2 px-3 border-b border-white/[0.04]"
                >
                  <span className="font-mono text-xs text-stone-300 truncate max-w-[240px]">
                    {p.path}
                  </span>
                  <span className="font-mono text-xs text-amber-400 font-bold">
                    {p.views} views
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* ── Footer ── */}
      <footer className="mt-12 text-center text-xs text-tan-dim font-mono">
        Resume Roast Founder Executive Desk · Authenticated Session Active · Zero 3rd-Party Trackers
      </footer>
    </div>
  )
}
