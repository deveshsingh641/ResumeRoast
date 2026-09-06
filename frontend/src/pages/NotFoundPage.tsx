import { Link } from 'react-router-dom'
import { usePageTitle } from '@/utils/usePageTitle'
import Footer from '@/components/Footer'

export default function NotFoundPage() {
  usePageTitle('404 Page Not Found')

  return (
    <main className="min-h-screen flex flex-col justify-between pt-12 pb-6 px-4 text-center">
      <div className="max-w-md mx-auto my-auto space-y-6 animate-fadeIn">
        {/* Paper Document Card with Red Stamp */}
        <div className="bg-[#191511] border border-white/[0.12] rounded-sm p-8 sm:p-10 shadow-2xl relative overflow-hidden text-left">
          {/* Top Bar */}
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-3 mb-6">
            <span className="font-mono text-[10px] text-tan-dim uppercase tracking-widest">
              DOC // ERROR 404
            </span>
            <span className="font-mono text-[10px] text-stamp font-bold uppercase tracking-wider bg-stamp/10 border border-stamp/30 px-2 py-0.5 rounded-sm">
              PAGE REJECTED
            </span>
          </div>

          {/* Stamp Header */}
          <div className="relative mb-6">
            <div className="border-3 border-stamp inline-block p-3 rounded-sm transform -rotate-3 bg-stamp/10 shadow-lg shadow-stamp/20 select-none">
              <span className="font-display text-4xl sm:text-5xl text-stamp tracking-tight leading-none">
                404
              </span>
              <p className="font-mono text-[10px] text-stamp font-bold tracking-widest uppercase mt-1">
                NOT FOUND // DESK EMPTY
              </p>
            </div>
          </div>

          {/* Recruiter Roast Message */}
          <div className="space-y-2">
            <h1 className="font-display text-xl sm:text-2xl text-paper tracking-tight">
              Yeh page desk pe mila hi nahi bhai.
            </h1>
            <p className="font-mono text-xs text-tan-dim leading-relaxed">
              Looks like this URL was filtered out by the ATS before it even reached the hiring manager. Your career doesn't have to share its fate.
            </p>
          </div>

          {/* Red-Pen Note */}
          <div className="mt-6 border-l-2 border-stamp pl-3 py-1 bg-stamp/5 rounded-r-sm">
            <p className="font-mono text-[11px] text-amber-300 italic">
              "Recruiter note: 0 matches found for this route. Recommend heading back to active grading desk immediately."
            </p>
          </div>

          {/* Action CTAs */}
          <div className="pt-6 border-t border-white/[0.08] flex flex-col sm:flex-row items-stretch gap-3">
            <Link to="/roast" className="btn-primary justify-center text-xs py-2.5 font-medium flex-1">
              Roast My Resume →
            </Link>
            <Link to="/" className="btn-ghost justify-center text-xs py-2.5 flex-1">
              Back to Desk
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-12">
        <Footer />
      </div>
    </main>
  )
}
