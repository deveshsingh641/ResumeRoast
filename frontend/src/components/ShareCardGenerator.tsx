import { useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import type { RoastResult } from '@/store/useAppStore'
import ScoreStamp from './ScoreStamp'

interface ShareCardGeneratorProps {
  result: RoastResult
}

export default function ShareCardGenerator({ result }: ShareCardGeneratorProps) {
  const offscreenCardRef = useRef<HTMLDivElement>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [downloaded, setDownloaded] = useState(false)
  const [shareNotice, setShareNotice] = useState<string | null>(null)

  const topRoast = result.issues[0]?.roast || result.one_line_verdict

  const whatsappShareText = `Bhai mera resume roast ho gaya 😂🔥!\n\nScore: ${result.overall_score}/100\nVerdict: "${result.one_line_verdict}"\n\nDekh tere resume ka kya banta hai: https://resumeroast.app`
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(whatsappShareText)}`

  const generateCanvas = async () => {
    if (!offscreenCardRef.current) return null
    try {
      return await html2canvas(offscreenCardRef.current, {
        width: 1200,
        height: 630,
        scale: 2,
        useCORS: true,
        backgroundColor: '#17140F',
        logging: false,
      })
    } catch {
      return null
    }
  }

  // B.1 WhatsApp-first sharing handler
  const handleWhatsAppShare = async () => {
    setIsGenerating(true)
    setShareNotice(null)
    try {
      const canvas = await generateCanvas()
      if (canvas && navigator.share && navigator.canShare) {
        canvas.toBlob(async (blob) => {
          if (blob) {
            const file = new File([blob], `resume-roast-${result.overall_score}.png`, {
              type: 'image/png',
            })
            if (navigator.canShare({ files: [file] })) {
              try {
                await navigator.share({
                  title: 'Resume Roast Score',
                  text: whatsappShareText,
                  files: [file],
                })
                setIsGenerating(false)
                return
              } catch {
                // Fallback to whatsapp link
              }
            }
          }
          window.open(whatsappUrl, '_blank')
          setIsGenerating(false)
        })
        return
      }
      // Desktop or standard fallback
      window.open(whatsappUrl, '_blank')
    } catch {
      window.open(whatsappUrl, '_blank')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = async () => {
    setIsGenerating(true)
    setShareNotice(null)
    try {
      const canvas = await generateCanvas()
      if (canvas) {
        const link = document.createElement('a')
        link.download = `resume-roast-score-${result.overall_score}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
        setDownloaded(true)
        setTimeout(() => setDownloaded(false), 3000)
      } else {
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(whatsappShareText)
          setShareNotice('Image render unavailable — share text copy ho gaya!')
          setTimeout(() => setShareNotice(null), 4000)
        }
      }
    } catch {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(whatsappShareText)
        setShareNotice('Verdict text copy ho gaya clipboard pe!')
        setTimeout(() => setShareNotice(null), 4000)
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopy = async () => {
    setIsGenerating(true)
    setShareNotice(null)
    try {
      const canvas = await generateCanvas()
      if (canvas && window.ClipboardItem && navigator.clipboard) {
        canvas.toBlob(async (blob) => {
          if (blob) {
            try {
              await navigator.clipboard.write([
                new ClipboardItem({ 'image/png': blob }),
              ])
              setCopied(true)
              setTimeout(() => setCopied(false), 3000)
            } catch {
              await navigator.clipboard.writeText(whatsappShareText)
              setCopied(true)
              setShareNotice('Roast summary copy ho gaya!')
              setTimeout(() => {
                setCopied(false)
                setShareNotice(null), 3000
              })
            }
          }
        })
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(whatsappShareText)
        setCopied(true)
        setShareNotice('Roast summary copy ho gaya!')
        setTimeout(() => {
          setCopied(false)
          setShareNotice(null), 3000
        })
      }
    } catch {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(whatsappShareText)
        setCopied(true)
        setTimeout(() => setCopied(false), 3000)
      }
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="w-full max-w-[640px] mx-auto text-left space-y-4">
      {/* ── Off-screen full-resolution 1200x630 card ── */}
      <div
        className="fixed"
        style={{ left: -9999, top: -9999, width: 1200, height: 630 }}
        aria-hidden="true"
      >
        <div
          ref={offscreenCardRef}
          style={{
            width: 1200,
            height: 630,
            backgroundColor: '#17140F',
            color: '#F5EFE0',
            fontFamily: 'Inter, sans-serif',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '72px 88px',
            boxSizing: 'border-box',
            overflow: 'hidden',
          }}
        >
          {/* Subtle desk border */}
          <div
            style={{
              position: 'absolute',
              inset: 24,
              border: '1px solid rgba(255, 255, 255, 0.08)',
              pointerEvents: 'none',
            }}
          />

          {/* Left content block */}
          <div style={{ flex: 1, paddingRight: 60 }}>
            <div
              style={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 14,
                color: '#FFB93C',
                letterSpacing: '2px',
                textTransform: 'uppercase',
                marginBottom: 20,
              }}
            >
              RESUMEROAST.APP // DESK KA OFFICIAL VERDICT
            </div>

            <div
              style={{
                fontFamily: '"Archivo Black", sans-serif',
                fontSize: 48,
                lineHeight: 1.0,
                color: '#F5EFE0',
                marginBottom: 28,
              }}
            >
              MERA RESUME HO GAYA <br />
              <span style={{ color: '#E8422D' }}>ROAST 🔥</span>
            </div>

            <div
              style={{
                fontFamily: 'Inter, sans-serif',
                fontSize: 20,
                lineHeight: 1.5,
                color: '#C9BFA6',
                borderLeft: '3px solid #E8422D',
                paddingLeft: 20,
                maxWidth: 540,
              }}
            >
              "{topRoast}"
            </div>
          </div>

          {/* Right stamp block */}
          <div style={{ flexShrink: 0 }}>
            <ScoreStamp
              score={result.overall_score}
              band={result.band}
              animate={false}
              size="lg"
              rotation={-12}
            />
          </div>

          {/* Bottom URL */}
          <div
            style={{
              position: 'absolute',
              bottom: 40,
              left: 88,
              fontFamily: '"IBM Plex Mono", monospace',
              fontSize: 13,
              color: '#8A8168',
            }}
          >
            Apna resume bhi roast karwao 👉 resumeroast.app
          </div>
        </div>
      </div>

      {/* ── Live Preview Card on Screen ── */}
      <div className="bg-bg border border-white/[0.08] rounded-sm p-6 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex-1 text-left">
            <p className="section-label mb-2">Share card preview</p>
            <p className="font-display text-xl text-paper leading-tight">
              Mera resume ho gaya <span className="text-stamp">roast.</span>
            </p>
            <p className="font-mono text-xs text-tan-dim mt-2 line-clamp-2">
              "{topRoast}"
            </p>
          </div>

          <div className="shrink-0">
            <ScoreStamp
              score={result.overall_score}
              band={result.band}
              animate={false}
              size="sm"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons — WhatsApp First Priority */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* B.1 Primary Button: WhatsApp Status */}
        <button
          type="button"
          onClick={handleWhatsAppShare}
          disabled={isGenerating}
          className="btn-primary flex-1 justify-center !bg-emerald-600 hover:!bg-emerald-500 !border-emerald-500 font-bold text-sm tracking-wide flex items-center gap-2"
        >
          <span>Status pe daal de</span>
          <span>📲</span>
        </button>

        <button
          type="button"
          onClick={handleDownload}
          disabled={isGenerating}
          className="btn-ghost flex-1 justify-center"
        >
          {downloaded ? '✓ Downloaded PNG' : isGenerating ? 'Generating…' : 'Download card'}
        </button>

        <button
          type="button"
          onClick={handleCopy}
          disabled={isGenerating}
          className="btn-ghost px-4 justify-center"
        >
          {copied ? '✓ Copied!' : 'Copy'}
        </button>
      </div>

      {shareNotice && (
        <p className="font-mono text-xs text-ember text-center">
          {shareNotice}
        </p>
      )}
    </div>
  )
}
