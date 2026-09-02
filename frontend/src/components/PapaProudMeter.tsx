import { useId } from 'react'

interface PapaProudMeterProps {
  overallScore: number
}

export function getPapaScore(score: number): number {
  // Deterministic gag score calculation based on real score
  if (score <= 20) return 14
  if (score <= 40) return Math.round(score * 0.75)
  if (score <= 65) return Math.min(68, Math.round(score * 0.85))
  if (score <= 85) return Math.min(84, Math.round(score * 0.92))
  return Math.min(95, score)
}

export function getPapaCommentary(papaScore: number): { comment: string; sub: string; emoji: string } {
  if (papaScore <= 25) {
    return {
      comment: 'Sharma ji ka beta dekh ke has raha hai abhi 💀',
      sub: 'Papa ko mat dikhana, seedha ghar se bahar nikal denge.',
      emoji: '💀',
    }
  }
  if (papaScore <= 45) {
    return {
      comment: 'Isse dikhake papa ko impress karna mushkil hai abhi 😭',
      sub: 'Papa bolenge: "Itne saal padhayi karwai aur ye summary likhi hai?"',
      emoji: '😭',
    }
  }
  if (papaScore <= 65) {
    return {
      comment: 'Papa bolenge: "Beta engineering karke yahi likha hai?" 🫠',
      sub: 'Passable hai, lekin unka chehra fir bhi thoda disappointed rahega.',
      emoji: '🫠',
    }
  }
  if (papaScore <= 80) {
    return {
      comment: 'Thoda theek hai, par bolenge: "aur 10% aa sakte the" 🤨',
      sub: 'Indian parents kabhi 100% khush nahi hote bhai, tu bhi jaanta hai.',
      emoji: '🤨',
    }
  }
  return {
    comment: 'Finally rishta pakka karne layak score aaya hai! 🎉',
    sub: 'Chalo colony mein mithai baantne ki taiyyari shuru karo.',
    emoji: '🎉',
  }
}

export default function PapaProudMeter({ overallScore }: PapaProudMeterProps) {
  const meterId = useId()
  const papaScore = getPapaScore(overallScore)
  const { comment, sub, emoji } = getPapaCommentary(papaScore)

  const meterColor =
    papaScore < 40 ? '#E8422D' : papaScore < 70 ? '#FFB93C' : '#7FA65C'

  const shareText = `Bhai mera Papa Proud Meter score sirf ${papaScore}% aaya hai ${emoji}!\n"${comment}"\nApna bhi check karwa: https://resumeroast.app`
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareText)}`

  return (
    <div className="w-full max-w-[640px] mx-auto bg-[#1A1612] border border-amber-500/20 rounded-sm p-6 text-left relative overflow-hidden shadow-lg">
      {/* Background subtle watermark */}
      <div
        className="absolute -right-4 -bottom-6 text-7xl select-none opacity-10 pointer-events-none"
        aria-hidden="true"
      >
        👨‍👧‍👦
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">👨‍💼</span>
          <div>
            <span className="font-mono text-[10px] text-amber-400 uppercase tracking-widest font-bold block">
              GAG METER // DIL PE MAT LENA
            </span>
            <h3 className="font-display text-lg sm:text-xl text-paper">
              Papa Proud Meter
            </h3>
          </div>
        </div>

        <div className="flex items-baseline gap-1 bg-black/40 border border-white/10 px-3 py-1 rounded-sm">
          <span
            className="font-display text-2xl font-bold"
            style={{ color: meterColor }}
          >
            {papaScore}%
          </span>
          <span className="font-mono text-[10px] text-tan-dim uppercase">PROUD</span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="w-full h-3 bg-black/50 border border-white/10 rounded-full overflow-hidden p-0.5 mb-4">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${papaScore}%`,
            backgroundColor: meterColor,
            boxShadow: `0 0 10px ${meterColor}60`,
          }}
        />
      </div>

      {/* Funny Commentary */}
      <div className="space-y-1">
        <p className="font-body text-sm font-semibold text-paper leading-snug">
          "{comment}"
        </p>
        <p className="font-mono text-xs text-tan-dim leading-relaxed">
          {sub}
        </p>
      </div>

      {/* WhatsApp mini share CTA */}
      <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center justify-between gap-4">
        <span className="font-mono text-[11px] text-tan-dim">
          Family group mein mat bhejna 💀
        </span>
        <a
          href={whatsappUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-xs text-emerald-400 hover:text-emerald-300 inline-flex items-center gap-1.5 transition-colors font-semibold"
        >
          <span>WhatsApp pe daal de</span>
          <span>📲</span>
        </a>
      </div>
    </div>
  )
}
