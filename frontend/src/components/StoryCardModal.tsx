import { useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import type { RoastResult } from '@/store/useAppStore'
import ScoreStamp from './ScoreStamp'

interface StoryCardModalProps {
  isOpen: boolean
  onClose: () => void
  result: RoastResult
}

export default function StoryCardModal({ isOpen, onClose, result }: StoryCardModalProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [isDownloading, setIsDownloading] = useState(false)
  const [copied, setCopied] = useState(false)
  const [downloaded, setDownloaded] = useState(false)

  if (!isOpen) return null

  const topRoast = result.issues?.[0]?.roast || result.one_line_verdict
  const worstQuote = result.issues?.[0]?.quoted_text || result.one_line_verdict

  const generateCanvas = async () => {
    if (!cardRef.current) return null
    try {
      return await html2canvas(cardRef.current, {
        width: 1080,
        height: 1920,
        scale: 2,
        useCORS: true,
        backgroundColor: '#0F0D0A',
        logging: false,
      })
    } catch (e) {
      console.error('Failed to render story canvas', e)
      return null
    }
  }

  const handleDownload = async () => {
    setIsDownloading(true)
    try {
      const canvas = await generateCanvas()
      if (canvas) {
        const link = document.createElement('a')
        link.download = `resume-roast-story-${result.overall_score}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
        setDownloaded(true)
        setTimeout(() => setDownloaded(false), 3000)
      }
    } finally {
      setIsDownloading(false)
    }
  }

  const handleShare = async () => {
    setIsDownloading(true)
    try {
      const canvas = await generateCanvas()
      if (canvas && navigator.share && navigator.canShare) {
        canvas.toBlob(async (blob) => {
          if (blob) {
            const file = new File([blob], `resume-roast-story-${result.overall_score}.png`, {
              type: 'image/png',
            })
            if (navigator.canShare({ files: [file] })) {
              try {
                await navigator.share({
                  title: 'Resume Roast 9:16 Story',
                  text: `Mera resume roast ho gaya 😂! Score: ${result.overall_score}/100\nVerdict: "${result.one_line_verdict}"\nCheck yours at https://resumeroast.app`,
                  files: [file],
                })
                setIsDownloading(false)
                return
              } catch {
                // fall through
              }
            }
          }
          window.open(
            `https://api.whatsapp.com/send?text=${encodeURIComponent(
              `Mera resume roast ho gaya 😂! Score: ${result.overall_score}/100\n"${result.one_line_verdict}"\nDekh tere resume ka kya banta hai 👉 https://resumeroast.app`
            )}`,
            '_blank'
          )
          setIsDownloading(false)
        })
        return
      }
      window.open(
        `https://api.whatsapp.com/send?text=${encodeURIComponent(
          `Mera resume roast ho gaya 😂! Score: ${result.overall_score}/100\n"${result.one_line_verdict}"\nDekh tere resume ka kya banta hai 👉 https://resumeroast.app`
        )}`,
        '_blank'
      )
    } finally {
      setIsDownloading(false)
    }
  }

  const handleCopy = async () => {
    setIsDownloading(true)
    try {
      const canvas = await generateCanvas()
      if (canvas && window.ClipboardItem && navigator.clipboard) {
        canvas.toBlob(async (blob) => {
          if (blob) {
            try {
              await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })])
              setCopied(true)
              setTimeout(() => setCopied(false), 3000)
            } catch {
              const text = `Score: ${result.overall_score}/100 | "${result.one_line_verdict}" | resumeroast.app`
              await navigator.clipboard.writeText(text)
              setCopied(true)
              setTimeout(() => setCopied(false), 3000)
            }
          }
        })
      }
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-md bg-[#17140F] border border-white/10 rounded-lg shadow-2xl p-6 my-8 text-left">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/10 mb-4">
          <div>
            <h3 className="font-display text-lg text-paper flex items-center gap-2">
              <span>📱</span>
              <span>Story Card (9:16)</span>
            </h3>
            <p className="font-mono text-xs text-tan-dim">
              Instagram & WhatsApp Story ke liye ready card
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-tan-dim hover:text-paper font-mono text-lg p-1.5 hover:bg-white/5 rounded-sm transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Scaled Visual Preview Container */}
        <div className="w-full flex justify-center py-2">
          <div
            className="w-[270px] h-[480px] rounded-md overflow-hidden shadow-2xl border border-white/15 relative bg-[#0F0D0A] flex flex-col justify-between p-4 select-none"
            style={{ aspectRatio: '9/16' }}
          >
            {/* Top Bar */}
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
              <span className="font-mono text-[9px] text-stamp font-bold tracking-widest uppercase">
                🔥 RESUME ROAST // 2026
              </span>
              <span className="font-mono text-[9px] text-amber-400 font-bold">
                SCORE: {result.overall_score}/100
              </span>
            </div>

            {/* Middle Stamp & Verdict */}
            <div className="flex flex-col items-center text-center my-auto space-y-3">
              <div className="transform scale-90 -rotate-6">
                <ScoreStamp score={result.overall_score} band={result.band} animate={false} size="md" />
              </div>

              <div className="bg-red-950/40 border border-red-500/30 rounded px-3 py-2">
                <p className="font-mono text-[9px] text-red-300 uppercase tracking-wider font-semibold">
                  OFFICIAL RED-PEN VERDICT
                </p>
                <p className="font-display text-sm text-paper font-bold mt-0.5 leading-snug line-clamp-3">
                  "{result.one_line_verdict}"
                </p>
              </div>

              {/* Crime quote snippet */}
              <div className="w-full bg-[#1F1B15] border-l-2 border-amber-500/70 p-2 text-left rounded-r">
                <p className="font-mono text-[8px] text-tan-dim uppercase">EVIDENCE FROM RESUME</p>
                <p className="font-mono text-[10px] text-paper/90 italic line-clamp-2 mt-0.5">
                  "{worstQuote}"
                </p>
                <p className="font-body text-[9px] text-amber-300 font-semibold mt-1 line-clamp-1">
                  ✍️ {topRoast}
                </p>
              </div>
            </div>

            {/* Bottom Brand Watermark */}
            <div className="border-t border-white/10 pt-2 flex items-center justify-between text-[9px] font-mono text-tan-dim">
              <span>👉 resumeroast.app</span>
              <span className="text-paper/80 font-bold">Free AI Roast 💀</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid grid-cols-2 gap-2.5 mt-5">
          <button
            type="button"
            onClick={handleDownload}
            disabled={isDownloading}
            className="btn-primary justify-center text-xs py-2.5 !bg-amber-500 hover:!bg-amber-400 !text-ink font-bold"
          >
            {downloaded ? '✓ Saved PNG!' : isDownloading ? 'Rendering…' : '📥 Download 9:16'}
          </button>

          <button
            type="button"
            onClick={handleShare}
            disabled={isDownloading}
            className="btn-primary justify-center text-xs py-2.5 !bg-emerald-600 hover:!bg-emerald-500 font-bold"
          >
            📲 WhatsApp Story
          </button>

          <button
            type="button"
            onClick={handleCopy}
            disabled={isDownloading}
            className="btn-ghost justify-center text-xs py-2 col-span-2"
          >
            {copied ? '✓ Image Copied!' : '📋 Copy to Clipboard'}
          </button>
        </div>
      </div>

      {/* ── Offscreen Full-Resolution (1080x1920) Story Card Container for HTML2Canvas ── */}
      <div
        className="fixed"
        style={{ left: -9999, top: -9999, width: 1080, height: 1920 }}
        aria-hidden="true"
      >
        <div
          ref={cardRef}
          style={{
            width: 1080,
            height: 1920,
            backgroundColor: '#0F0D0A',
            backgroundImage:
              'radial-gradient(circle at 50% 20%, rgba(232, 66, 45, 0.15), transparent 60%), radial-gradient(circle at 80% 80%, rgba(255, 185, 60, 0.1), transparent 50%)',
            padding: 80,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            boxSizing: 'border-box',
            fontFamily: '"Space Grotesk", sans-serif',
            color: '#F5EFE6',
          }}
        >
          {/* Header */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '2px solid rgba(255, 255, 255, 0.12)',
              paddingBottom: 32,
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 24,
                  fontWeight: 800,
                  letterSpacing: '4px',
                  color: '#E8422D',
                }}
              >
                🔥 RESUME ROAST // 2026
              </div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 18,
                  color: '#8A8168',
                  marginTop: 6,
                }}
              >
                CONFIDENTIAL AUDIT DOSSIER
              </div>
            </div>

            <div
              style={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 24,
                fontWeight: 700,
                color: '#FFB93C',
                backgroundColor: 'rgba(255, 185, 60, 0.1)',
                padding: '10px 24px',
                borderRadius: 8,
                border: '1px solid rgba(255, 185, 60, 0.3)',
              }}
            >
              FINAL GRADE
            </div>
          </div>

          {/* Centerpiece Content */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: 48,
              margin: 'auto 0',
            }}
          >
            {/* Score Stamp Large */}
            <div style={{ transform: 'scale(2.2) rotate(-8deg)', margin: '40px 0' }}>
              <ScoreStamp score={result.overall_score} band={result.band} animate={false} size="lg" />
            </div>

            {/* One Line Verdict Banner */}
            <div
              style={{
                backgroundColor: 'rgba(232, 66, 45, 0.15)',
                border: '3px solid rgba(232, 66, 45, 0.4)',
                borderRadius: 16,
                padding: '36px 44px',
                maxWidth: 920,
              }}
            >
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 20,
                  fontWeight: 700,
                  color: '#FF8A7A',
                  letterSpacing: '3px',
                  textTransform: 'uppercase',
                  marginBottom: 16,
                }}
              >
                OFFICIAL RED-PEN VERDICT
              </div>
              <div
                style={{
                  fontSize: 38,
                  fontWeight: 800,
                  lineHeight: 1.35,
                  color: '#FFF8F0',
                }}
              >
                "{result.one_line_verdict}"
              </div>
            </div>

            {/* Evidence Paper Scrap */}
            <div
              style={{
                width: '100%',
                maxWidth: 920,
                backgroundColor: '#1C1814',
                borderLeft: '8px solid #FFB93C',
                borderRadius: '0 16px 16px 0',
                padding: '36px 44px',
                textAlign: 'left',
                boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
              }}
            >
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 18,
                  fontWeight: 700,
                  color: '#FFB93C',
                  letterSpacing: '2px',
                  textTransform: 'uppercase',
                  marginBottom: 12,
                }}
              >
                EVIDENCE EXTRACTED FROM RESUME
              </div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 24,
                  color: '#D4CDC3',
                  fontStyle: 'italic',
                  lineHeight: 1.5,
                  marginBottom: 20,
                }}
              >
                "{worstQuote}"
              </div>
              <div
                style={{
                  fontSize: 24,
                  fontWeight: 600,
                  color: '#FF8A7A',
                  lineHeight: 1.4,
                }}
              >
                ✍️ {topRoast}
              </div>
            </div>
          </div>

          {/* Footer Call to Action & Watermark */}
          <div
            style={{
              borderTop: '2px solid rgba(255, 255, 255, 0.12)',
              paddingTop: 36,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 26,
                  fontWeight: 700,
                  color: '#F5EFE6',
                }}
              >
                resumeroast.app
              </div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 18,
                  color: '#8A8168',
                  marginTop: 6,
                }}
              >
                Apna resume bacha le before HR rejects it 💀
              </div>
            </div>

            <div
              style={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 22,
                fontWeight: 800,
                color: '#17140F',
                backgroundColor: '#F5EFE6',
                padding: '14px 28px',
                borderRadius: 8,
              }}
            >
              ROAST YOURS FREE
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
