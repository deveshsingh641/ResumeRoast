interface PaperSkeletonProps {
  label?: string
}

export default function PaperSkeleton({ label = 'Desk pe report taiyyar ho rahi hai…' }: PaperSkeletonProps) {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-6 text-center select-none relative overflow-hidden">
      {/* Tilted placeholder paper sheet */}
      <div
        className="w-full max-w-[540px] bg-paper/90 rounded-sm p-8 sm:p-10 shadow-2xl relative transition-all animate-pulse"
        style={{
          transform: 'rotate(-1.5deg)',
          border: '1px solid rgba(0,0,0,0.12)',
        }}
      >
        {/* Paper subtle lines */}
        <div
          className="absolute inset-0 pointer-events-none opacity-[0.04]"
          style={{
            backgroundImage:
              'repeating-linear-gradient(transparent, transparent 20px, #2B2620 20px, #2B2620 21px)',
          }}
          aria-hidden="true"
        />

        {/* Placeholder Candidate Header */}
        <div className="border-b border-black/10 pb-4 mb-6 text-left space-y-2">
          <div className="h-5 w-44 bg-[#2B2620]/20 rounded-xs" />
          <div className="h-3 w-32 bg-[#2B2620]/15 rounded-xs" />
        </div>

        {/* Placeholder Bullets with dashed red pen outlines */}
        <div className="space-y-4 text-left">
          <div className="relative p-2 border border-dashed border-stamp/40 rounded-xs bg-stamp/[0.03]">
            <div className="h-3 w-full bg-[#2B2620]/20 rounded-xs mb-2" />
            <div className="h-3 w-3/4 bg-[#2B2620]/15 rounded-xs" />
          </div>

          <div className="relative p-2 border border-dashed border-amber-500/40 rounded-xs bg-amber-500/[0.03]">
            <div className="h-3 w-full bg-[#2B2620]/20 rounded-xs mb-2" />
            <div className="h-3 w-2/3 bg-[#2B2620]/15 rounded-xs" />
          </div>

          <div className="relative p-2 border border-dashed border-stamp/40 rounded-xs bg-stamp/[0.03]">
            <div className="h-3 w-5/6 bg-[#2B2620]/20 rounded-xs" />
          </div>
        </div>

        {/* Watermark Rubber Stamp Placeholder */}
        <div className="absolute -top-4 -right-4 w-28 h-28 rounded-full border-4 border-dashed border-stamp/30 flex items-center justify-center rotate-[-12deg]">
          <span className="font-mono text-[10px] text-stamp/40 tracking-widest uppercase font-bold">
            GRADING…
          </span>
        </div>
      </div>

      {/* Monospace status caption below paper */}
      <div className="mt-8 flex items-center gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-stamp animate-ping" />
        <p className="font-mono text-xs text-tan-dim tracking-wider uppercase">
          {label}
        </p>
      </div>
    </main>
  )
}
