import { Link, useSearchParams } from 'react-router-dom'
import ResumeUploader from '@/components/ResumeUploader'
import { useAppStore } from '@/store/useAppStore'

export default function RoastPage() {
  const { uploadError } = useAppStore()
  const [searchParams] = useSearchParams()
  const isUpgraded = searchParams.get('upgraded') === 'true'

  return (
    <main className="min-h-screen flex flex-col justify-between p-6 desk-cursor">
      {/* Top Bar */}
      <header className="max-w-[960px] w-full mx-auto flex items-center justify-between">
        <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
          RESUME<span className="text-stamp">ROAST</span>
        </Link>
        <Link to="/" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
          ← Wapas Desk Pe
        </Link>
      </header>

      {/* Center Dropzone / Grading Area */}
      <div className="max-w-[560px] w-full mx-auto text-center my-auto py-12">
        <p className="section-label mb-3">DESK PE DOCUMENT RAKHO</p>
        <h1 className="font-display text-3xl sm:text-4xl text-paper tracking-tight mb-3">
          Apna resume desk pe daal de bhai.
        </h1>
        <p className="font-mono text-xs text-tan-dim mb-8">
          Red pen taiyyar hai. Kadak grading milegi aur exact bullet rewrites bhi.
        </p>

        {/* Pro Active Celebration Banner */}
        {isUpgraded && (
          <div className="mb-6 bg-emerald-950/40 border border-emerald-500/40 rounded-sm p-4 text-left flex items-center gap-3">
            <span className="text-2xl">🎉</span>
            <div>
              <p className="font-display text-sm text-emerald-300 font-bold">
                Pro Subscription Active!
              </p>
              <p className="font-mono text-xs text-tan-dim mt-0.5">
                Unlimited daily roasts aur full 5–8 issues breakdown unlock ho chuka hai.
              </p>
            </div>
          </div>
        )}

        {/* Morphable Dropzone Component */}
        <ResumeUploader />

        {/* Global rate limit / server error note */}
        {uploadError && (
          <div
            role="alert"
            className="mt-4 border border-stamp/40 bg-[#E8422D]/[0.08] rounded-sm p-4 text-left"
          >
            <p className="font-mono text-xs text-stamp leading-relaxed">
              ⚠ {uploadError}
            </p>
            {uploadError.includes('limit') && (
              <Link to="/pricing" className="font-mono text-xs text-ember underline mt-2 inline-block">
                Pro unlimited plan dekho →
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Bottom Info Note */}
      <footer className="max-w-[960px] w-full mx-auto text-center font-mono text-xs text-tan-dim py-4 border-t border-white/[0.08]">
        Har din 1 free roast · Text PDF ya DOCX · Anonymous files 7 din mein automatically delete ho jaati hain
      </footer>
    </main>
  )
}
