import { useRef, useState } from 'react'
import html2canvas from 'html2canvas'
import ScoreStamp from './ScoreStamp'
import type { ScoreBand } from '@/store/useAppStore'

interface BattleData {
  id: string
  winner: string
  margin: string
  verdict: string
  fighter_1: {
    name: string
    overall_score: number
    band: ScoreBand
    one_line_verdict: string
  }
  fighter_2: {
    name: string
    overall_score: number
    band: ScoreBand
    one_line_verdict: string
  }
  fighter_1_best_line?: string
  fighter_2_best_line?: string
}

interface BattleShareCardProps {
  battle: BattleData
}

export default function BattleShareCard({ battle }: BattleShareCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [downloaded, setDownloaded] = useState(false)
  const [copied, setCopied] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  const shareText = `Resume Roast Battle Result 🥊\nFighter 1: ${battle.fighter_1.overall_score}/100\nFighter 2: ${battle.fighter_2.overall_score}/100\n\nVerdict: "${battle.verdict}"\n\nBattle your friends at: https://resumeroast.app/battle`

  const generateCanvas = async () => {
    if (!cardRef.current) return null
    try {
      return await html2canvas(cardRef.current, {
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

  const handleDownload = async () => {
    setIsGenerating(true)
    try {
      const canvas = await generateCanvas()
      if (canvas) {
        const link = document.createElement('a')
        link.download = `resume-battle-${battle.id.slice(0, 8)}.png`
        link.href = canvas.toDataURL('image/png')
        link.click()
        setDownloaded(true)
        setTimeout(() => setDownloaded(false), 3000)
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(shareText)
        setDownloaded(true)
        setTimeout(() => setDownloaded(false), 3000)
      }
    } catch {
      if (navigator.clipboard) {
        await navigator.clipboard.writeText(shareText)
      }
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopy = async () => {
    setIsGenerating(true)
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
              await navigator.clipboard.writeText(shareText)
              setCopied(true)
              setTimeout(() => setCopied(false), 3000)
            }
          }
        })
      } else if (navigator.clipboard) {
        await navigator.clipboard.writeText(shareText)
        setCopied(true)
        setTimeout(() => setCopied(false), 3000)
      }
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="w-full max-w-[640px] mx-auto text-left space-y-4">
      {/* Off-screen 1200x630 VS Battle Canvas */}
      <div
        className="fixed"
        style={{ left: -9999, top: -9999, width: 1200, height: 630 }}
        aria-hidden="true"
      >
        <div
          ref={cardRef}
          style={{
            width: 1200,
            height: 630,
            backgroundColor: '#17140F',
            color: '#F5EFE0',
            fontFamily: 'Inter, sans-serif',
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: '54px 72px',
            boxSizing: 'border-box',
            overflow: 'hidden',
          }}
        >
          {/* Top header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div
              style={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 15,
                color: '#FFB93C',
                letterSpacing: '2px',
                textTransform: 'uppercase',
              }}
            >
              RESUMEROAST.APP // OFFICIAL ROAST BATTLE
            </div>
            <div
              style={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: 14,
                color: '#E8422D',
                fontWeight: 700,
              }}
            >
              1-ON-1 HEAD TO HEAD
            </div>
          </div>

          {/* Center fighters & VS */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-around', margin: '20px 0' }}>
            {/* Fighter 1 */}
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 14, color: '#C9BFA6', marginBottom: 8 }}>
                FIGHTER 1
              </div>
              <div style={{ display: 'inline-block' }}>
                <ScoreStamp score={battle.fighter_1.overall_score} band={battle.fighter_1.band} animate={false} size="lg" />
              </div>
            </div>

            {/* VS Badge */}
            <div style={{ textAlign: 'center', padding: '0 30px' }}>
              <div
                style={{
                  fontFamily: '"Archivo Black", sans-serif',
                  fontSize: 52,
                  color: '#E8422D',
                  lineHeight: 1,
                  textShadow: '0 0 20px rgba(232, 66, 45, 0.4)',
                }}
              >
                VS
              </div>
              <div
                style={{
                  fontFamily: '"IBM Plex Mono", monospace',
                  fontSize: 12,
                  color: '#FFB93C',
                  textTransform: 'uppercase',
                  marginTop: 6,
                }}
              >
                {battle.margin}
              </div>
            </div>

            {/* Fighter 2 */}
            <div style={{ textAlign: 'center', flex: 1 }}>
              <div style={{ fontFamily: '"IBM Plex Mono", monospace', fontSize: 14, color: '#C9BFA6', marginBottom: 8 }}>
                FIGHTER 2
              </div>
              <div style={{ display: 'inline-block' }}>
                <ScoreStamp score={battle.fighter_2.overall_score} band={battle.fighter_2.band} animate={false} size="lg" />
              </div>
            </div>
          </div>

          {/* Bottom Verdict Banner */}
          <div
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.04)',
              borderLeft: '4px solid #E8422D',
              padding: '16px 24px',
              borderRadius: 4,
            }}
          >
            <div style={{ fontFamily: 'Inter, sans-serif', fontSize: 18, color: '#F5EFE0', lineHeight: 1.4 }}>
              "{battle.verdict}"
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-3">
        <button
          type="button"
          onClick={handleDownload}
          disabled={isGenerating}
          className="btn-primary flex-1 justify-center"
        >
          {downloaded ? '✓ Downloaded Battle Card' : isGenerating ? 'Generating…' : 'Download Battle Card (PNG)'}
        </button>

        <button
          type="button"
          onClick={handleCopy}
          disabled={isGenerating}
          className="btn-ghost flex-1 justify-center"
        >
          {copied ? '✓ Copied to Clipboard!' : 'Copy Battle Card'}
        </button>
      </div>
    </div>
  )
}
