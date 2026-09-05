import { useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import type { RoastResult } from '@/store/useAppStore'
import ScoreStamp from './ScoreStamp'

interface ShareCardGeneratorProps {
  result: RoastResult
}

type CardStyle = 'verdict' | 'torn_paper'

export default function ShareCardGenerator({ result }: ShareCardGeneratorProps) {
  const offscreenCardRef = useRef<HTMLDivElement>(null)
  const [cardStyle, setCardStyle] = useState<CardStyle>('verdict')
  const [isGenerating, setIsGenerating] = useState(false)
  const [copied, setCopied] = useState(false)
  const [downloaded, setDownloaded] = useState(false)
  const [shareNotice, setShareNotice] = useState<string | null>(null)

  const topRoast = result.issues[0]?.roast || result.one_line_verdict
  const worstQuote = result.issues[0]?.quoted_text || result.one_line_verdict

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
        backgroundColor: cardStyle === 'torn_paper' ? '#17140F' : '#17140F',
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
            const file = new File([blob], `resume-roast-${cardStyle}-${result.overall_score}.png`, {
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
        link.download = `resume-roast-${cardStyle}-${result.overall_score}.png`
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
                setShareNotice(null)
              }, 3000)
            }
          }
        })
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(whatsappShareText)
        setCopied(true)
        setShareNotice('Roast summary copy ho gaya!')
        setTimeout(() => {
          setCopied(false)
          setShareNotice(null)
        }, 3000)
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
      {/* 2.3 Visual Card Style Selector Toggle */}
      <div className="flex items-center justify-between gap-2 border-b border-white/[0.08] pb-3">
        <span className="font-mono text-xs text-tan-dim uppercase tracking-wider">
          Card Style Chuno:
        </span>
        <div className="flex items-center gap-1.5 p-1 bg-white/[0.04] border border-white/[0.08] rounded-sm">
          <button
            type="button"
            onClick={() => setCardStyle('verdict')}
            className={`font-mono text-xs px-3 py-1 rounded-xs transition-all ${
              cardStyle === 'verdict'
                ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/40'
                : 'text-tan-dim hover:text-paper'
            }`}
          >
            📋 Desk Verdict
          </button>
          <button
            type="button"
            onClick={() => setCardStyle('torn_paper')}
            className={`font-mono text-xs px-3 py-1 rounded-xs transition-all ${
              cardStyle === 'torn_paper'
                ? 'bg-amber-500/20 text-amber-300 font-semibold border border-amber-500/40'
                : 'text-tan-dim hover:text-paper'
            }`}
          >
            📄 Torn Paper Scrap
          </button>
        </div>
      </div>

      {/* ── Off-screen full-resolution 1200x630 card ── */}
      <div
        className="fixed"
        style={{ left: -9999, top: -9999, width: 1200, height: 630 }}
        aria-hidden="true"
      >
        {cardStyle === 'verdict' ? (
          /* Style 1: Desk Verdict (Dark Charcoal Theme) */
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
            <div
              style={{
                position: 'absolute',
                inset: 24,
                border: '1px solid rgba(255, 255, 255, 0.08)',
                pointerEvents: 'none',
              }}
            />

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

            <div style={{ flexShrink: 0 }}>
              <ScoreStamp
                score={result.overall_score}
                band={result.band}
                animate={false}
                size="lg"
                rotation={-12}
              />
            </div>

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
        ) : (
          /* Style 2: 2.3 Torn-Out Page Scrap from the Resume */
          <div
            ref={offscreenCardRef}
            style={{
              width: 1200,
              height: 630,
              backgroundColor: '#17140F',
              padding: '28px 48px',
              boxSizing: 'border-box',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* The Torn Paper Sheet with ragged top edge */}
            <div
              className="ragged-top-edge"
              style={{
                width: '100%',
                height: '100%',
                backgroundColor: '#F5EFE0',
                color: '#2B2620',
                padding: '52px 64px 40px 64px',
                boxSizing: 'border-box',
                position: 'relative',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
              }}
            >
              {/* Ruled lines */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  backgroundImage:
                    'repeating-linear-gradient(transparent, transparent 28px, #2B2620 28px, #2B2620 29px)',
                  opacity: 0.04,
                  pointerEvents: 'none',
                }}
              />

              {/* Top Row: Candidate Excerpt & Official Title */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div
                      style={{
                        fontFamily: '"IBM Plex Mono", monospace',
                        fontSize: 12,
                        color: '#E8422D',
                        fontWeight: 'bold',
                        letterSpacing: '2px',
                        textTransform: 'uppercase',
                        marginBottom: 6,
                      }}
                    >
                      CONFIDENTIAL // EVIDENCE OF CAREER DAMAGE
                    </div>
                    <div
                      style={{
                        fontFamily: '"IBM Plex Mono", monospace',
                        fontSize: 22,
                        fontWeight: 700,
                        color: '#2B2620',
                        letterSpacing: '1px',
                      }}
                    >
                      SUBMITTED RESUME [EXCERPT]
                    </div>
                  </div>

                  {/* Stamp overlaid on the torn paper */}
                  <div style={{ transform: 'rotate(-10deg)', marginTop: -10 }}>
                    <ScoreStamp
                      score={result.overall_score}
                      band={result.band}
                      animate={false}
                      size="md"
                    />
                  </div>
                </div>

                {/* Quoted flawed line with red pen annotation */}
                <div style={{ marginTop: 24, maxWidth: 740 }}>
                  <div
                    style={{
                      fontFamily: '"IBM Plex Mono", monospace',
                      fontSize: 16,
                      color: '#2B2620',
                      backgroundColor: 'rgba(232, 66, 45, 0.08)',
                      border: '1.5px dashed #E8422D',
                      padding: '12px 20px',
                      borderRadius: 4,
                      lineHeight: 1.5,
                    }}
                  >
                    "{worstQuote}"
                  </div>

                  {/* Red pen verdict */}
                  <div
                    style={{
                      fontFamily: 'Inter, sans-serif',
                      fontSize: 24,
                      fontWeight: 600,
                      color: '#E8422D',
                      marginTop: 18,
                      lineHeight: 1.3,
                    }}
                  >
                    ✍️ Red Pen: "{result.one_line_verdict}"
                  </div>
                </div>
              </div>

              {/* Bottom footer link */}
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderTop: '1px solid rgba(43, 38, 32, 0.15)',
                  paddingTop: 12,
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 12,
                  color: '#8A8168',
                }}
              >
                <span>TORN FROM DESK ARCHIVES</span>
                <span>resumeroast.app 👉 apna resume bacha le</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Live Preview Card on Screen ── */}
      {cardStyle === 'verdict' ? (
        <div className="bg-bg border border-white/[0.08] rounded-sm p-6 relative overflow-hidden transition-all">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="flex-1 text-left">
              <p className="section-label mb-2">Desk Verdict Card Preview</p>
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
      ) : (
        <div className="bg-[#17140F] p-4 border border-white/[0.08] rounded-sm relative overflow-hidden">
          <div className="ragged-top-edge bg-paper text-ink p-5 rounded-xs relative shadow-lg">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-[10px] text-stamp font-bold tracking-wider uppercase mb-1">
                  EVIDENCE OF CAREER DAMAGE
                </p>
                <p className="font-mono text-xs text-ink font-semibold line-clamp-2 bg-stamp/[0.07] border border-dashed border-stamp/40 p-2 rounded-xs">
                  "{worstQuote}"
                </p>
                <p className="font-body text-xs text-stamp font-semibold mt-2 line-clamp-1">
                  ✍️ "{result.one_line_verdict}"
                </p>
              </div>
              <div className="shrink-0 -mt-1 -mr-1">
                <ScoreStamp
                  score={result.overall_score}
                  band={result.band}
                  animate={false}
                  size="sm"
                  rotation={-10}
                />
              </div>
            </div>
          </div>
        </div>
      )}

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
