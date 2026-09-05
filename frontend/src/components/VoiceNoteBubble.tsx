import { useState, useRef } from 'react'
import axios from 'axios'
import { getCurrentLanguage } from '@/i18n'

interface VoiceNoteBubbleProps {
  roastId: string
  oneLineVerdict?: string
}

// 32 stylized vertical bars with authentic WhatsApp voice message height variations
const WAVEFORM_HEIGHTS = [
  6, 12, 20, 8, 16, 26, 14, 22, 30, 12, 18, 24, 10, 16, 28, 20, 14, 26, 12, 18,
  30, 16, 22, 10, 14, 20, 8, 16, 10, 14, 8, 4,
]

export default function VoiceNoteBubble({ roastId, oneLineVerdict }: VoiceNoteBubbleProps) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [loading, setLoading] = useState(false)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [script, setScript] = useState<string | null>(null)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Generate or fetch voice roast
  const handleGenerateVoice = async () => {
    const lang = getCurrentLanguage()
    try {
      setLoading(true)
      setError(null)
      const { data } = await axios.post(`/api/roast/${roastId}/voice?lang=${lang}`)
      setAudioUrl(data.audio_url)
      setScript(data.script)
      if (data.duration_seconds) setDuration(data.duration_seconds)

      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {})
        }
      }, 200)
    } catch {
      setError(
        lang === 'hi-IN'
          ? 'Voice roast generate karne mein dikkat aayi. Kripya dubara try karein.'
          : 'Could not generate voice roast note. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const togglePlay = () => {
    if (!audioUrl) {
      handleGenerateVoice()
      return
    }

    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {})
    }
  }

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime)
      if (audioRef.current.duration && !isNaN(audioRef.current.duration)) {
        setDuration(Math.round(audioRef.current.duration))
      }
    }
  }

  const handleAudioEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
  }

  const handleSeek = (index: number) => {
    if (audioRef.current && duration > 0) {
      const targetTime = (index / WAVEFORM_HEIGHTS.length) * duration
      audioRef.current.currentTime = targetTime
      setCurrentTime(targetTime)
    }
  }

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60)
    const s = Math.floor(secs % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className="w-full max-w-[560px] mx-auto text-left my-4">
      <div className="flex items-center justify-between mb-2">
        <p className="section-label">WHATSAPP VOICE NOTE ROAST</p>
        <span className="font-mono text-[10px] text-ember tracking-wider flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-stamp animate-pulse" />
          VOICE MEMO
        </span>
      </div>

      {/* ── WhatsApp Voice Bubble Container: --paper background on dark screen ── */}
      <div
        className="relative bg-paper text-ink rounded-full px-4 py-3 sm:px-5 sm:py-3.5 shadow-paper border border-black/10 select-none transition-transform active:scale-[0.995]"
        style={{
          boxShadow: '0 20px 40px rgba(0,0,0,0.35)',
        }}
      >
        <div className="flex items-center gap-3 sm:gap-4">
          {/* Play/Pause Button in --stamp fill with --paper icon */}
          <button
            type="button"
            onClick={togglePlay}
            aria-label={isPlaying ? 'Pause voice roast' : 'Play voice roast'}
            className="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-stamp hover:bg-stamp-hover text-paper flex items-center justify-center shrink-0 transition-transform active:scale-95 shadow-sm"
          >
            {isPlaying ? (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
              </svg>
            ) : (
              <svg className="w-4 h-4 translate-x-0.5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          {/* Waveform & Duration */}
          <div className="flex-1 min-w-0 flex flex-col justify-center">
            {/* Waveform Bars */}
            <div
              className={`flex items-center gap-[2px] sm:gap-[2.5px] h-8 cursor-pointer select-none py-1 ${
                loading ? 'animate-pulse opacity-60' : ''
              }`}
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect()
                const clickX = e.clientX - rect.left
                const ratio = Math.max(0, Math.min(1, clickX / rect.width))
                if (audioRef.current && duration > 0) {
                  audioRef.current.currentTime = ratio * duration
                  setCurrentTime(ratio * duration)
                }
              }}
            >
              {WAVEFORM_HEIGHTS.map((height, idx) => {
                const barProgress = (idx / WAVEFORM_HEIGHTS.length) * 100
                const isPassed = barProgress <= progressPercent
                return (
                  <div
                    key={idx}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleSeek(idx)
                    }}
                    style={{ height: `${height}px` }}
                    className={`w-[3px] rounded-full transition-colors duration-150 ${
                      isPassed ? 'bg-stamp' : 'bg-tan-dim/50 hover:bg-tan-dim'
                    }`}
                  />
                )
              })}
            </div>

            {/* Time counter + WhatsApp Double Tick in --ink */}
            <div className="flex items-center justify-between text-[11px] font-mono text-ink/75 pt-0.5">
              <span>{formatTime(currentTime > 0 ? currentTime : duration)}</span>

              <div className="flex items-center gap-1.5">
                <span className="text-[10px] text-ink/60">Voice memo</span>
                {/* Double tick read receipt in Cyan/Blue (#53BDEB) */}
                <span className="text-[#34B7F1] font-bold text-xs select-none">✓✓</span>
              </div>
            </div>
          </div>
        </div>

        {/* Hidden Audio Element */}
        {audioUrl && (
          <audio
            ref={audioRef}
            src={audioUrl.startsWith('http') ? audioUrl : `${import.meta.env.VITE_API_URL || ''}${audioUrl}`}
            onTimeUpdate={handleTimeUpdate}
            onEnded={handleAudioEnded}
            preload="metadata"
          />
        )}
      </div>

      {/* Script preview & actions */}
      {script && (
        <div className="mt-2.5 px-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-1.5 text-left">
          <p className="font-mono text-xs text-tan italic line-clamp-1">
            "{script}"
          </p>
          {audioUrl && (
            <a
              href={audioUrl.startsWith('http') ? audioUrl : `${import.meta.env.VITE_API_URL || ''}${audioUrl}`}
              download={`resume-roast-voice-${roastId}.mp3`}
              className="shrink-0 text-[11px] font-mono text-ember hover:underline flex items-center gap-1"
            >
              <span>📥 Download MP3</span>
            </a>
          )}
        </div>
      )}

      {error && (
        <div className="mt-2.5 text-center">
          <p className="font-mono text-xs text-stamp">{error}</p>
          <button
            type="button"
            onClick={handleGenerateVoice}
            className="font-mono text-xs text-amber-300 hover:underline mt-1 inline-block"
          >
            ↻ Retry generating audio
          </button>
        </div>
      )}

      {/* Safety Disclaimer */}
      <p className="font-mono text-[11px] text-tan-dim mt-2 text-center">
        ⚠️ AI-generated voice, for fun — not a real recruiter.
      </p>
    </div>
  )
}
