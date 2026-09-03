/**
 * Web Audio API synthesizer for subtle physical sound design.
 * Provides paper rustle, stamp slam thud, and confetti pop without external audio files.
 */

let audioCtx: AudioContext | null = null

function getAudioContext(): AudioContext | null {
  if (typeof window === 'undefined') return null
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
    if (AudioContextClass) {
      audioCtx = new AudioContextClass()
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume().catch(() => {})
  }
  return audioCtx
}

export function isSoundEnabled(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('resume_roast_sound_enabled') === 'true'
}

export function setSoundEnabled(enabled: boolean): void {
  if (typeof window === 'undefined') return
  localStorage.setItem('resume_roast_sound_enabled', enabled ? 'true' : 'false')
  if (enabled) {
    getAudioContext()
  }
}

/**
 * 1. Soft paper-rustle sound as resume lands on desk
 */
export function playPaperRustle(): void {
  if (!isSoundEnabled()) return
  const ctx = getAudioContext()
  if (!ctx) return

  try {
    const bufferSize = ctx.sampleRate * 0.22 // 220ms
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate)
    const data = buffer.getChannelData(0)

    // Generate shaped white noise
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize)
    }

    const noise = ctx.createBufferSource()
    noise.buffer = buffer

    // Low-pass filter to sound like soft fibrous paper, not harsh hiss
    const filter = ctx.createBiquadFilter()
    filter.type = 'bandpass'
    filter.frequency.setValueAtTime(900, ctx.currentTime)
    filter.Q.setValueAtTime(1.2, ctx.currentTime)

    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0.01, ctx.currentTime)
    gain.gain.exponentialRampToValueAtTime(0.12, ctx.currentTime + 0.04)
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.22)

    noise.connect(filter)
    filter.connect(gain)
    gain.connect(ctx.destination)

    noise.start()
  } catch {
    // Audio playback error silently ignored
  }
}

/**
 * 2. Satisfying physical rubber stamp thud
 */
export function playStampThud(): void {
  if (!isSoundEnabled()) return
  const ctx = getAudioContext()
  if (!ctx) return

  try {
    const now = ctx.currentTime

    // Low punch oscillator
    const osc = ctx.createOscillator()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(110, now)
    osc.frequency.exponentialRampToValueAtTime(28, now + 0.16)

    const oscGain = ctx.createGain()
    oscGain.gain.setValueAtTime(0.35, now)
    oscGain.gain.exponentialRampToValueAtTime(0.001, now + 0.18)

    osc.connect(oscGain)
    oscGain.connect(ctx.destination)

    // Transient slap click
    const clickSize = ctx.sampleRate * 0.02
    const clickBuffer = ctx.createBuffer(1, clickSize, ctx.sampleRate)
    const clickData = clickBuffer.getChannelData(0)
    for (let i = 0; i < clickSize; i++) {
      clickData[i] = (Math.random() * 2 - 1) * Math.exp(-i / (clickSize * 0.2))
    }

    const click = ctx.createBufferSource()
    click.buffer = clickBuffer

    const clickFilter = ctx.createBiquadFilter()
    clickFilter.type = 'lowpass'
    clickFilter.frequency.setValueAtTime(1200, now)

    const clickGain = ctx.createGain()
    clickGain.gain.setValueAtTime(0.18, now)
    clickGain.gain.exponentialRampToValueAtTime(0.001, now + 0.02)

    click.connect(clickFilter)
    clickFilter.connect(clickGain)
    clickGain.connect(ctx.destination)

    osc.start(now)
    click.start(now)
    osc.stop(now + 0.2)
  } catch {
    // Silently ignore
  }
}

/**
 * 3. Light festive pop when confetti triggers
 */
export function playConfettiPop(): void {
  if (!isSoundEnabled()) return
  const ctx = getAudioContext()
  if (!ctx) return

  try {
    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(320, now)
    osc.frequency.exponentialRampToValueAtTime(880, now + 0.09)

    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0.18, now)
    gain.gain.exponentialRampToValueAtTime(0.001, now + 0.14)

    osc.connect(gain)
    gain.connect(ctx.destination)

    osc.start(now)
    osc.stop(now + 0.15)
  } catch {
    // Silently ignore
  }
}
