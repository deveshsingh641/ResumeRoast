import { Link } from 'react-router-dom'
import ResumeUploader from '@/components/ResumeUploader'
import { useAppStore } from '@/store/useAppStore'

export default function RoastPage() {
  const { uploadError } = useAppStore()

  return (
    <main className="min-h-screen flex flex-col justify-between p-6 desk-cursor">
      {/* Top Bar */}
      <header className="max-w-[960px] w-full mx-auto flex items-center justify-between">
        <Link to="/" className="font-display text-lg tracking-tight text-paper select-none">
          RESUME<span className="text-stamp">ROAST</span>
        </Link>
        <Link to="/" className="font-mono text-xs text-tan-dim hover:text-tan transition-colors">
          ← Back to Desk
        </Link>
      </header>

      {/* Center Dropzone / Grading Area */}
      <div className="max-w-[560px] w-full mx-auto text-center my-auto py-12">
        <p className="section-label mb-3">DOCUMENT SUBMISSION</p>
        <h1 className="font-display text-3xl sm:text-4xl text-paper tracking-tight mb-3">
          Place your resume on the desk.
        </h1>
        <p className="font-mono text-xs text-tan-dim mb-8">
          The red pen is ready. You will receive a brutal grade and exact rewrites.
        </p>

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
                View Pro unlimited plan →
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Bottom Info Note */}
      <footer className="max-w-[960px] w-full mx-auto text-center font-mono text-xs text-tan-dim py-4 border-t border-white/[0.08]">
        Free daily roast · Text-based PDF or DOCX · Anonymous files automatically purged after 7 days
      </footer>
    </main>
  )
}
