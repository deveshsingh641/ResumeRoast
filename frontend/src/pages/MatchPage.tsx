import React, { useState, useEffect, useRef } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { normalizeLang } from '@/i18n/detector'
import LanguageSwitcher from '@/components/LanguageSwitcher'
import Footer from '@/components/Footer'
import WaitlistModal from '@/components/WaitlistModal'
import { useAppStore } from '@/store/useAppStore'
import { usePageTitle } from '@/utils/usePageTitle'

interface MissingKeyword {
  keyword: string
  importance: 'critical' | 'high' | 'nice-to-have'
  roast: string
}

interface IrrelevantClutter {
  quoted_text: string
  roast: string
}

interface TailoredRewrite {
  original: string
  tailored_fix: string
  target_jd_requirement: string
}

interface MatchResultData {
  match_score: number
  ats_status: 'rejected' | 'borderline' | 'shortlisted'
  verdict: string
  job_title: string
  company_name: string
  matched_skills: string[]
  missing_keywords: MissingKeyword[]
  total_missing_keywords: number
  irrelevant_clutter: IrrelevantClutter[]
  tailored_bullet_rewrites: TailoredRewrite[]
  total_tailored_rewrites: number
  is_truncated: boolean
  is_pro: boolean
}

interface SampleJD {
  id: string
  title: string
  company: string
  description: string
}

const FALLBACK_SAMPLES: SampleJD[] = [
  {
    id: 'swiggy-frontend',
    title: 'Frontend Engineer (React / TypeScript)',
    company: 'Swiggy',
    description: `Role: Frontend Engineer II
Location: Bengaluru / Remote
About the role:
We are looking for a high-energy Frontend Engineer to build consumer-facing interfaces handling 10M+ daily active users.

Key Requirements:
- 2+ years experience with React.js, TypeScript, Next.js, and Modern JavaScript (ES6+).
- Strong command of state management (Zustand, Redux Toolkit) and React Query.
- Proven track record optimizing Web Vitals (LCP, FID, CLS), code-splitting, and render performance.
- Experience with Tailwind CSS, responsive design, and cross-browser quirks.
- Automated testing experience with Jest, React Testing Library, or Playwright.
- Excellent debugging skills with Chrome DevTools, Network profiling, and Sentry monitoring.`,
  },
  {
    id: 'zerodha-backend',
    title: 'Backend SDE (Go / PostgreSQL / Redis)',
    company: 'Zerodha',
    description: `Role: Software Development Engineer — Core Trading Backend
Location: Bengaluru
About the role:
Build resilient, ultra-low-latency financial systems that process billions of rupees in market transactions daily with zero downtime.

Key Requirements:
- 2+ years of hands-on backend engineering with Go (Golang), Python, or C++.
- Deep expertise in relational databases (PostgreSQL): query optimization, indexing, transaction isolation levels, and connection pooling.
- High-throughput caching and pub/sub architecture using Redis or Kafka.
- Microservices communication with gRPC, Protocol Buffers, and REST.
- Linux systems programming: profiling CPU/memory bottlenecks, goroutine leak detection, and network sockets.
- Docker, Kubernetes, and automated CI/CD deployment pipelines.`,
  },
  {
    id: 'ai-startup-fullstack',
    title: 'Full Stack AI Engineer',
    company: 'NextGen AI Lab',
    description: `Role: Full Stack AI Engineer
Location: Remote / Delhi NCR
About the role:
Join an early-stage venture-backed AI startup building generative workflows and autonomous agents for enterprise software teams.

Key Requirements:
- Full-stack fluency across TypeScript/React (frontend) and Python/FastAPI (backend).
- Hands-on experience integrating LLM APIs (OpenAI, Anthropic Claude, Gemini) and LangChain/LlamaIndex.
- Vector databases (Pinecone, Qdrant, pgvector) for RAG pipelines and semantic search.
- Clean API design, async task queues with Celery or Redis, and PostgreSQL.
- Rapid prototyping mindset: ship MVPs in days, iterate based on user telemetry.`,
  },
]

const PROCESSING_STAGES = [
  'Reading resume & target job specifications…',
  'Running ATS parser & extracting core technical skills…',
  'Grilling keyword gaps against role expectations…',
  'Simulating recruiter 6-second eye-tracking scan…',
  'Drafting tailored red-pen bullet rewrites…',
  'Finalizing ATS Reality Check report…',
]

export default function MatchPage() {
  usePageTitle('Job Description Match & ATS Gap Scanner')
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { i18n } = useTranslation()
  const isHinglish = normalizeLang(i18n.language) === 'hi-IN'

  const { result: existingRoast } = useAppStore()

  // Form State
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [useExistingRoast, setUseExistingRoast] = useState<boolean>(false)
  const [roastIdParam, setRoastIdParam] = useState<string | null>(null)
  const [jobTitle, setJobTitle] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [samples, setSamples] = useState<SampleJD[]>(FALLBACK_SAMPLES)
  const [selectedSampleId, setSelectedSampleId] = useState<string | null>(null)

  // Execution State
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingStageIdx, setProcessingStageIdx] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [matchResult, setMatchResult] = useState<MatchResultData | null>(null)
  const [copiedRewriteIndex, setCopiedRewriteIndex] = useState<number | null>(null)
  const [copiedFullReport, setCopiedFullReport] = useState(false)
  const [showWaitlist, setShowWaitlist] = useState(false)
  const [activeKeywordPopover, setActiveKeywordPopover] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  // Detect query param roast_id or use current stored roast
  useEffect(() => {
    const qRoastId = searchParams.get('roast_id')
    if (qRoastId) {
      setRoastIdParam(qRoastId)
      setUseExistingRoast(true)
    } else if (existingRoast?.id) {
      setRoastIdParam(existingRoast.id)
      setUseExistingRoast(true)
    }
  }, [searchParams, existingRoast])

  // Fetch sample JDs from backend
  useEffect(() => {
    axios
      .get('/api/match/samples')
      .then((res) => {
        if (res.data?.samples && Array.isArray(res.data.samples) && res.data.samples.length > 0) {
          setSamples(res.data.samples)
        }
      })
      .catch(() => {
        // Fallback already pre-loaded
      })
  }, [])

  // Progress animation cycle
  useEffect(() => {
    if (!isProcessing) return
    const interval = setInterval(() => {
      setProcessingStageIdx((prev) => (prev < PROCESSING_STAGES.length - 1 ? prev + 1 : prev))
    }, 2800)
    return () => clearInterval(interval)
  }, [isProcessing])

  const handleSelectSample = (sample: SampleJD) => {
    setSelectedSampleId(sample.id)
    setJobTitle(sample.title)
    setCompanyName(sample.company)
    setJobDescription(sample.description)
    setErrorMessage(null)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setErrorMessage(
          isHinglish
            ? 'File size 5MB se chhota hona chahiye.'
            : 'File size exceeds 5MB limit. Please upload a smaller document.'
        )
        return
      }
      setResumeFile(file)
      setUseExistingRoast(false)
      setErrorMessage(null)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (isProcessing) return
    const file = e.dataTransfer.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setErrorMessage(
          isHinglish
            ? 'File size 5MB se chhota hona chahiye.'
            : 'File size exceeds 5MB limit. Please upload a smaller document.'
        )
        return
      }
      setResumeFile(file)
      setUseExistingRoast(false)
      setErrorMessage(null)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isProcessing) return

    if (!jobDescription || jobDescription.trim().length < 30) {
      setErrorMessage(
        isHinglish
          ? 'Kripya poora Job Description paste karein (kam se kam 30 characters).'
          : 'Please paste a complete Job Description (at least 30 characters).'
      )
      return
    }

    if (!resumeFile && !useExistingRoast) {
      setErrorMessage(
        isHinglish
          ? 'Kripya apna resume upload karein ya previous roast use karein.'
          : 'Please upload a resume document or select your recent roast.'
      )
      return
    }

    setIsProcessing(true)
    setProcessingStageIdx(0)
    setErrorMessage(null)
    setMatchResult(null)

    try {
      let response
      if (resumeFile) {
        const formData = new FormData()
        formData.append('file', resumeFile)
        formData.append('job_description', jobDescription)
        if (jobTitle) formData.append('job_title', jobTitle)
        if (companyName) formData.append('company_name', companyName)
        formData.append('language', isHinglish ? 'hi-IN' : 'en-US')

        response = await axios.post('/api/match', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 45000,
        })
      } else {
        response = await axios.post(
          '/api/match',
          {
            roast_id: roastIdParam,
            job_description: jobDescription,
            job_title: jobTitle,
            company_name: companyName,
            language: isHinglish ? 'hi-IN' : 'en-US',
          },
          { timeout: 45000 }
        )
      }

      setMatchResult(response.data)
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message
      setErrorMessage(
        detail ||
          (isHinglish
            ? 'JD match analyze karne mein dikkat aayi. Kripya dobara koshish karein.'
            : 'Failed to analyze JD match. Please try again.')
      )
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCopyRewrite = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedRewriteIndex(index)
      setTimeout(() => setCopiedRewriteIndex(null), 2500)
    } catch {
      // fallback
    }
  }

  const handleCopyFullReport = async () => {
    if (!matchResult) return
    const lines = [
      `ATS REALITY CHECK REPORT — ${matchResult.job_title} @ ${matchResult.company_name}`,
      `Match Score: ${matchResult.match_score}/100 [Status: ${matchResult.ats_status.toUpperCase()}]`,
      `Recruiter Verdict: "${matchResult.verdict}"`,
      '',
      '--- MATCHED SKILLS ---',
      matchResult.matched_skills.map((s) => `✓ ${s}`).join('\n'),
      '',
      '--- CRITICAL MISSING KEYWORDS ---',
      matchResult.missing_keywords
        .map((k) => `✗ [${k.importance.toUpperCase()}] ${k.keyword}: ${k.roast}`)
        .join('\n'),
      '',
      '--- TAILORED BULLET REWRITES ---',
      matchResult.tailored_bullet_rewrites
        .map(
          (rw, i) =>
            `#${i + 1} Target: ${rw.target_jd_requirement}\nOriginal: "${rw.original}"\nTailored: "${rw.tailored_fix}"\n`
        )
        .join('\n'),
      'Analyzed via Resume Roast (https://resumeroast.app/match)',
    ]
    try {
      await navigator.clipboard.writeText(lines.join('\n'))
      setCopiedFullReport(true)
      setTimeout(() => setCopiedFullReport(false), 2500)
    } catch {
      // fallback
    }
  }

  return (
    <main className="min-h-screen flex flex-col justify-between p-4 sm:p-6 desk-cursor">
      {/* Top Header */}
      <header className="max-w-[1040px] w-full mx-auto flex items-center justify-between py-2">
        <Link to="/" className="font-display text-lg sm:text-xl tracking-tight text-paper select-none">
          RESUME<span className="text-stamp">ROAST</span>
        </Link>
        <div className="flex items-center gap-4">
          <Link to="/" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
            {isHinglish ? '← Desk Pe Wapas' : '← Back to Desk'}
          </Link>
          <LanguageSwitcher />
        </div>
      </header>

      {/* Sub-Tab Switcher */}
      <div className="max-w-[1040px] w-full mx-auto mt-4 mb-8">
        <div className="flex items-center justify-center gap-2 p-1.5 bg-white/[0.03] border border-white/[0.08] rounded-sm max-w-md mx-auto">
          <Link
            to="/roast"
            className="flex-1 py-2 px-3 text-center font-mono text-xs text-tan-dim hover:text-tan transition-colors rounded-sm hover:bg-white/[0.03]"
          >
            🔥 {isHinglish ? 'General Roast' : 'General Roast'}
          </Link>
          <div className="flex-1 py-2 px-3 text-center font-mono text-xs font-bold text-paper bg-stamp/20 border border-stamp/40 rounded-sm shadow-sm">
            🎯 {isHinglish ? 'JD Match Mode (NEW)' : 'JD Match Mode (NEW)'}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="max-w-[1040px] w-full mx-auto flex-1">
        {/* Hero Title */}
        <div className="text-center mb-8">
          <p className="section-label mb-2">
            {isHinglish ? 'ATS REALITY CHECK & ROLE TAILORING' : 'ATS REALITY CHECK & ROLE TAILORING'}
          </p>
          <h1 className="font-display text-2xl sm:text-4xl text-paper tracking-tight mb-2">
            {isHinglish
              ? 'Pata karo tumhara resume ATS mein reject kyun hoga.'
              : 'Find out exactly why your dream ATS will reject you.'}
          </h1>
          <p className="font-mono text-xs sm:text-sm text-tan-dim max-w-xl mx-auto">
            {isHinglish
              ? 'Target company ka JD dalo. Missing keywords, irrelevant clutter aur exact bullet rewrites pao.'
              : 'Paste your target job description. Uncover missing keyword traps and get tailored drop-in bullet rewrites.'}
          </p>
        </div>

        {/* Input Form or Results Dashboard */}
        {!matchResult && !isProcessing && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Pane: Resume Source */}
              <div className="border border-white/[0.08] bg-[#1a1712] rounded-sm p-5 sm:p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="font-display text-sm text-paper flex items-center gap-2">
                      <span>📄 1. {isHinglish ? 'Resume Document' : 'Resume Document'}</span>
                    </label>
                    {roastIdParam && (
                      <span className="font-mono text-[11px] text-emerald-400 bg-emerald-950/40 px-2 py-0.5 border border-emerald-500/30 rounded-xs">
                        {isHinglish ? 'Recent roast linked' : 'Recent roast linked'}
                      </span>
                    )}
                  </div>

                  {/* Option to use recent roast if available */}
                  {roastIdParam && (
                    <div className="mb-4 p-3 bg-white/[0.04] border border-white/[0.1] rounded-sm flex items-center justify-between">
                      <div className="flex items-center gap-2.5">
                        <span className="text-xl">⚡</span>
                        <div>
                          <p className="font-mono text-xs text-paper font-semibold">
                            {isHinglish ? 'Roasted Resume Linked' : 'Recently Roasted Resume'}
                          </p>
                          <p className="font-mono text-[10px] text-tan-dim">
                            ID: {roastIdParam.slice(0, 8)}…
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setUseExistingRoast(true)}
                          className={`font-mono text-[11px] px-2.5 py-1 rounded-sm border transition-all ${
                            useExistingRoast
                              ? 'bg-stamp text-paper border-stamp font-bold'
                              : 'bg-transparent text-tan-dim border-white/20 hover:text-tan'
                          }`}
                        >
                          {useExistingRoast
                            ? isHinglish
                              ? '✓ Selected'
                              : '✓ Selected'
                            : isHinglish
                            ? 'Use This'
                            : 'Use This'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Drag-and-drop zone */}
                  <div
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={handleDrop}
                    onClick={() => fileInputRef.current?.click()}
                    className={`border-2 border-dashed rounded-sm p-6 text-center cursor-pointer transition-colors ${
                      resumeFile
                        ? 'border-emerald-500/60 bg-emerald-950/10'
                        : useExistingRoast
                        ? 'border-white/20 bg-white/[0.01]'
                        : 'border-white/20 hover:border-stamp/60 bg-white/[0.02]'
                    }`}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.docx"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    {resumeFile ? (
                      <div className="space-y-1">
                        <p className="font-mono text-xs text-emerald-400 font-bold">
                          ✓ {resumeFile.name}
                        </p>
                        <p className="font-mono text-[11px] text-tan-dim">
                          {(resumeFile.size / 1024).toFixed(0)} KB · Click to change file
                        </p>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <span className="text-3xl block">📥</span>
                        <p className="font-mono text-xs text-paper">
                          {isHinglish
                            ? 'PDF ya DOCX drop karein ya browse karein'
                            : 'Drop target resume (PDF/DOCX) or browse'}
                        </p>
                        <p className="font-mono text-[11px] text-tan-dim">
                          Max 5MB · Text-based PDF or DOCX
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-white/[0.06]">
                  <p className="font-mono text-[11px] text-tan-dim">
                    🔒 {isHinglish ? 'Aapka data 100% private rehta hai.' : 'Your resume is analyzed securely and never shared.'}
                  </p>
                </div>
              </div>

              {/* Right Pane: Target Job Description */}
              <div className="border border-white/[0.08] bg-[#1a1712] rounded-sm p-5 sm:p-6 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className="font-display text-sm text-paper flex items-center gap-2">
                      <span>🎯 2. {isHinglish ? 'Target Job Description (JD)' : 'Target Job Description (JD)'}</span>
                    </label>
                  </div>

                  {/* Sample Chips */}
                  <div className="mb-3">
                    <p className="font-mono text-[11px] text-tan-dim mb-1.5">
                      {isHinglish ? '1-Click Trial Chips (Sample JDs):' : 'Instant 1-Click Samples:'}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {samples.map((s) => (
                        <button
                          key={s.id}
                          type="button"
                          onClick={() => handleSelectSample(s)}
                          className={`font-mono text-[11px] px-2.5 py-1 rounded-sm border transition-all ${
                            selectedSampleId === s.id
                              ? 'bg-ember/20 border-ember text-ember font-bold'
                              : 'bg-white/[0.03] border-white/15 text-tan-dim hover:text-tan hover:border-white/30'
                          }`}
                        >
                          💼 {s.company} ({s.id.includes('frontend') ? 'Frontend' : s.id.includes('backend') ? 'Backend' : 'AI'})
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Role Title & Company Inputs */}
                  <div className="grid grid-cols-2 gap-2 mb-3">
                    <div>
                      <input
                        type="text"
                        placeholder={isHinglish ? 'Job Title (e.g. SDE II)' : 'Job Title (e.g. SDE II)'}
                        value={jobTitle}
                        onChange={(e) => setJobTitle(e.target.value)}
                        className="w-full bg-black/40 border border-white/15 rounded-sm px-3 py-1.5 font-mono text-xs text-paper focus:outline-none focus:border-stamp"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder={isHinglish ? 'Company (e.g. Swiggy)' : 'Company (e.g. Swiggy)'}
                        value={companyName}
                        onChange={(e) => setCompanyName(e.target.value)}
                        className="w-full bg-black/40 border border-white/15 rounded-sm px-3 py-1.5 font-mono text-xs text-paper focus:outline-none focus:border-stamp"
                      />
                    </div>
                  </div>

                  {/* JD Textarea */}
                  <textarea
                    rows={7}
                    placeholder={
                      isHinglish
                        ? 'LinkedIn, Naukri, ya Careers page se Job Description yahan paste karein…'
                        : 'Paste job description, requirements, and tech stack here from LinkedIn, Naukri, or Careers page…'
                    }
                    value={jobDescription}
                    onChange={(e) => {
                      setJobDescription(e.target.value)
                      setSelectedSampleId(null)
                    }}
                    className="w-full bg-black/40 border border-white/15 rounded-sm p-3 font-mono text-xs text-paper focus:outline-none focus:border-stamp leading-relaxed resize-y"
                  />
                </div>

                <div className="mt-2 flex items-center justify-between text-[11px] font-mono text-tan-dim">
                  <span>{jobDescription.length} characters</span>
                  <span>Min: 30 chars</span>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {errorMessage && (
              <div className="border border-stamp/40 bg-stamp/10 rounded-sm p-3.5 text-left font-mono text-xs text-stamp">
                ⚠ {errorMessage}
              </div>
            )}

            {/* Submit Action */}
            <div className="text-center pt-2">
              <button
                type="submit"
                disabled={isProcessing}
                className="btn-primary !py-3 !px-8 text-sm sm:text-base font-display tracking-wider uppercase shadow-lg shadow-stamp/20 hover:scale-[1.01] active:scale-[0.99] transition-transform"
              >
                🎯 {isHinglish ? 'ATS Reality Check Run Karo →' : 'Run ATS Reality Check →'}
              </button>
              <p className="font-mono text-[11px] text-tan-dim mt-2">
                {isHinglish
                  ? 'Free tier includes match score, brutal verdict, and top keywords gap breakdown'
                  : 'Free tier includes match score, brutal verdict, and top keywords gap breakdown'}
              </p>
            </div>
          </form>
        )}

        {/* Processing State Animation */}
        {isProcessing && (
          <div className="max-w-xl mx-auto border border-white/[0.08] bg-[#1a1712] rounded-sm p-8 text-center my-12 shadow-2xl">
            <div className="w-12 h-12 mx-auto mb-4 border-3 border-stamp border-t-transparent rounded-full animate-spin" />
            <p className="section-label mb-2">SIMULATING ATS PARSER</p>
            <h2 className="font-display text-lg sm:text-xl text-paper mb-3">
              {PROCESSING_STAGES[processingStageIdx]}
            </h2>
            <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mb-4">
              <div
                className="h-full bg-stamp transition-all duration-500 ease-out"
                style={{
                  width: `${((processingStageIdx + 1) / PROCESSING_STAGES.length) * 100}%`,
                }}
              />
            </div>
            <p className="font-mono text-xs text-tan-dim">
              Comparing your experience against target role requirements & ATS filters…
            </p>
          </div>
        )}

        {/* Results Dashboard */}
        {matchResult && !isProcessing && (
          <div className="space-y-8 animate-fadeIn">
            {/* Top Match Card */}
            <div className="border border-white/[0.08] bg-[#1a1712] rounded-sm p-6 sm:p-8">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-white/[0.08]">
                <div>
                  <span className="section-label mb-1">
                    {matchResult.company_name} · {matchResult.job_title}
                  </span>
                  <h2 className="font-display text-2xl sm:text-3xl text-paper">
                    ATS Reality Check Result
                  </h2>
                  <p className="font-mono text-xs text-tan-dim mt-1">
                    Screened against target job description requirements
                  </p>
                </div>

                {/* ATS Score Stamp */}
                <div
                  className={`border-3 p-4 rounded-sm text-center min-w-[170px] uppercase font-display select-none transform rotate-[-2deg] ${
                    matchResult.ats_status === 'rejected'
                      ? 'border-stamp text-stamp bg-stamp/10 shadow-lg shadow-stamp/20'
                      : matchResult.ats_status === 'shortlisted'
                      ? 'border-emerald-500 text-emerald-400 bg-emerald-950/30 shadow-lg shadow-emerald-500/20'
                      : 'border-ember text-ember bg-ember/10 shadow-lg shadow-ember/20'
                  }`}
                >
                  <p className="text-3xl sm:text-4xl tracking-tight leading-none">
                    {matchResult.match_score}%
                  </p>
                  <p className="text-xs tracking-widest mt-1 font-mono">
                    STATUS: {matchResult.ats_status}
                  </p>
                </div>
              </div>

              {/* Brutal Recruiter Verdict */}
              <div className="mt-6 bg-black/40 border border-white/[0.08] rounded-sm p-4 sm:p-5 flex items-start gap-4">
                <span className="text-2xl sm:text-3xl shrink-0">
                  {matchResult.ats_status === 'rejected'
                    ? '💀'
                    : matchResult.ats_status === 'shortlisted'
                    ? '🚀'
                    : '🧐'}
                </span>
                <div>
                  <p className="font-mono text-xs text-tan-dim uppercase tracking-wider mb-1">
                    Recruiter Verdict & ATS Reality:
                  </p>
                  <p className="font-mono text-sm sm:text-base text-paper leading-relaxed italic">
                    "{matchResult.verdict}"
                  </p>
                </div>
              </div>
            </div>

            {/* Keyword Matrix: Matched vs Missing */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Matched Skills */}
              <div className="border border-emerald-500/30 bg-emerald-950/10 rounded-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-display text-sm sm:text-base text-emerald-400 flex items-center gap-2">
                    <span>✓ Matched Qualifications</span>
                  </h3>
                  <span className="font-mono text-xs text-emerald-400/80 bg-emerald-950/60 px-2 py-0.5 rounded-xs border border-emerald-500/30">
                    {matchResult.matched_skills.length} found
                  </span>
                </div>
                <p className="font-mono text-xs text-tan-dim mb-4">
                  These verified skills and technologies were detected in both your resume and the JD.
                </p>
                <div className="flex flex-wrap gap-2">
                  {matchResult.matched_skills.map((skill, i) => (
                    <span
                      key={i}
                      className="font-mono text-xs px-2.5 py-1 bg-emerald-950/40 text-emerald-300 border border-emerald-500/40 rounded-sm"
                    >
                      ✓ {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Missing Critical Keywords */}
              <div className="border border-stamp/40 bg-stamp/5 rounded-sm p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-display text-sm sm:text-base text-stamp flex items-center gap-2">
                    <span>✗ Missing Critical Keywords</span>
                  </h3>
                  <span className="font-mono text-xs text-stamp bg-stamp/20 px-2 py-0.5 rounded-xs border border-stamp/40">
                    {matchResult.total_missing_keywords} missing
                  </span>
                </div>
                <p className="font-mono text-xs text-tan-dim mb-4">
                  Demanded in the JD but absent from your resume. Click tags to see why ATS auto-rejects:
                </p>
                <div className="flex flex-wrap gap-2 mb-4">
                  {matchResult.missing_keywords.map((kw, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() =>
                        setActiveKeywordPopover(activeKeywordPopover === kw.keyword ? null : kw.keyword)
                      }
                      className={`font-mono text-xs px-2.5 py-1 rounded-sm border transition-all text-left flex items-center gap-1.5 ${
                        activeKeywordPopover === kw.keyword
                          ? 'bg-stamp text-paper border-stamp font-bold scale-105'
                          : 'bg-stamp/10 text-stamp border-stamp/40 hover:border-stamp'
                      }`}
                    >
                      <span>⚠</span>
                      <span>{kw.keyword}</span>
                      <span className="text-[10px] opacity-70 uppercase">({kw.importance})</span>
                    </button>
                  ))}
                </div>

                {/* Popover / Detail for selected missing keyword */}
                {activeKeywordPopover && (
                  <div className="bg-black/60 border border-stamp/50 rounded-sm p-3.5 mt-2 animate-fadeIn text-left">
                    {(() => {
                      const item = matchResult.missing_keywords.find(
                        (k) => k.keyword === activeKeywordPopover
                      )
                      if (!item) return null
                      return (
                        <>
                          <div className="flex items-center justify-between text-xs font-mono mb-1">
                            <span className="font-bold text-stamp">{item.keyword}</span>
                            <span className="text-tan-dim uppercase text-[10px]">
                              Priority: {item.importance}
                            </span>
                          </div>
                          <p className="font-mono text-xs text-paper leading-relaxed">
                            {item.roast}
                          </p>
                        </>
                      )
                    })()}
                  </div>
                )}
              </div>
            </div>

            {/* Irrelevant Fluff / Clutter Section (if any) */}
            {matchResult.irrelevant_clutter && matchResult.irrelevant_clutter.length > 0 && (
              <div className="border border-ember/30 bg-ember/5 rounded-sm p-6">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-display text-sm sm:text-base text-ember flex items-center gap-2">
                    <span>⚠️ Irrelevant Resume Clutter</span>
                  </h3>
                  <span className="font-mono text-xs text-ember/80">
                    Wasting 1-page real estate
                  </span>
                </div>
                <p className="font-mono text-xs text-tan-dim mb-4">
                  These lines or sections have zero bearing on this specific role and dilute your core engineering impact:
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {matchResult.irrelevant_clutter.map((clutter, i) => (
                    <div key={i} className="bg-black/40 border border-ember/20 rounded-sm p-3">
                      <p className="font-mono text-xs text-paper font-semibold mb-1">
                        "{clutter.quoted_text}"
                      </p>
                      <p className="font-mono text-xs text-tan-dim">{clutter.roast}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tailored Red-Pen Rewrites (The Pro Upsell Hook) */}
            <div className="border border-white/[0.08] bg-[#1a1712] rounded-sm p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
                <div>
                  <span className="section-label mb-1">ROLE-SPECIFIC RED-PEN REWRITES</span>
                  <h3 className="font-display text-xl sm:text-2xl text-paper">
                    Tailored Bullet Point Transformations
                  </h3>
                  <p className="font-mono text-xs text-tan-dim mt-1">
                    Adapted directly to target this JD's language, technologies, and measurable scale.
                  </p>
                </div>
                {matchResult.tailored_bullet_rewrites.length > 0 && (
                  <button
                    type="button"
                    onClick={handleCopyFullReport}
                    className="btn-ghost !text-xs !py-1.5 !px-3 font-mono text-paper"
                  >
                    {copiedFullReport ? '✓ Report Copied!' : '📋 Copy All Report'}
                  </button>
                )}
              </div>

              {/* Rewrites Cards */}
              <div className="space-y-5">
                {matchResult.tailored_bullet_rewrites.map((rw, i) => (
                  <div
                    key={i}
                    className="border border-white/[0.08] bg-black/40 rounded-sm p-5 relative group"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono text-[11px] text-ember uppercase tracking-wider">
                        Target Requirement: {rw.target_jd_requirement}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleCopyRewrite(rw.tailored_fix, i)}
                        className="font-mono text-xs text-tan-dim hover:text-emerald-400 transition-colors flex items-center gap-1"
                      >
                        {copiedRewriteIndex === i ? '✓ Copied to clipboard' : 'Copy Rewrite ⎘'}
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Original Weak Bullet */}
                      <div className="border-l-2 border-stamp/60 pl-3 py-1 bg-stamp/5 rounded-r-sm">
                        <p className="font-mono text-[10px] text-stamp uppercase mb-1">
                          Original Weak Bullet:
                        </p>
                        <p className="font-mono text-xs text-tan-dim line-through leading-relaxed">
                          "{rw.original}"
                        </p>
                      </div>

                      {/* Tailored Drop-In Rewrite */}
                      <div className="border-l-2 border-emerald-500 pl-3 py-1 bg-emerald-950/20 rounded-r-sm">
                        <p className="font-mono text-[10px] text-emerald-400 uppercase mb-1 font-bold">
                          Tailored for this JD:
                        </p>
                        <p className="font-mono text-xs text-paper leading-relaxed">
                          "{rw.tailored_fix}"
                        </p>
                      </div>
                    </div>
                  </div>
                ))}

                {/* Locked Pro State / Waitlist Hook */}
                {matchResult.is_truncated && (
                  <div className="border border-stamp/40 bg-gradient-to-b from-stamp/10 to-transparent rounded-sm p-6 text-center space-y-3 relative overflow-hidden">
                    <div className="text-3xl">🔒</div>
                    <h4 className="font-display text-lg text-paper">
                      3 Additional Tailored Rewrites & Full Keyword Gap Matrix
                    </h4>
                    <p className="font-mono text-xs text-tan-dim max-w-md mx-auto">
                      Unlock all role-specific metrics, quantified impact bullets, and full ATS pass guarantee.
                    </p>
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={() => setShowWaitlist(true)}
                        className="btn-primary !py-2.5 !px-6 text-xs font-mono tracking-wider uppercase inline-flex items-center gap-2"
                      >
                        <span>Pro Launching Soon 🔜 (Join Waitlist →)</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
              <button
                type="button"
                onClick={() => {
                  setMatchResult(null)
                  setJobDescription('')
                  setSelectedSampleId(null)
                }}
                className="btn-ghost !text-xs font-mono"
              >
                ← Match Another Job Description
              </button>
              <Link to="/roast" className="btn-ghost !text-xs font-mono">
                🔥 Go to General Roast
              </Link>
              <Link to="/battle" className="btn-ghost !text-xs font-mono">
                ⚔️ Try 1-on-1 Battle
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-16">
        <Footer />
      </div>

      {/* Pro Waitlist Modal */}
      <WaitlistModal
        isOpen={showWaitlist}
        onClose={() => setShowWaitlist(false)}
        source="jd_match_mode"
        headline="Pro Launching Soon 🔜"
        subheadline="All tailored bullet rewrites, deep ATS keyword matrix, and unlimited JD matches unlock the moment Pro goes live. Join the waitlist for launch priority and early-bird pricing."
      />
    </main>
  )
}
