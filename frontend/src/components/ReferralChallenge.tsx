import { useState } from 'react'

export default function ReferralChallenge() {
  const [copied, setCopied] = useState(false)
  const challengeLink = 'https://resumeroast.app'
  const shareMessage = `Bhai apna resume test karwa ke dikha, dekhein kiska score zyada bura hai 😂🔥: ${challengeLink}`
  const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(shareMessage)}`

  const handleCopy = async () => {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(shareMessage)
      setCopied(true)
      setTimeout(() => setCopied(false), 3000)
    }
  }

  return (
    <div className="w-full max-w-[640px] mx-auto bg-[#1A1612] border border-amber-500/20 rounded-sm p-6 text-left relative overflow-hidden">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex-1">
          <div className="inline-flex items-center gap-1.5 font-mono text-[10px] text-amber-400 font-bold uppercase tracking-wider mb-1">
            <span>🔥 DARE CHALLENGE</span>
          </div>
          <h4 className="font-display text-base sm:text-lg text-paper mb-1">
            3 dosto ko roast karwao, apna next roast free mein full unlock ho jayega
          </h4>
          <p className="font-mono text-xs text-tan-dim leading-relaxed">
            WhatsApp group mein link phenko aur dekho kiske resume ka band bajta hai.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-2 shrink-0 w-full sm:w-auto">
          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary !py-2 !px-4 !text-xs !bg-emerald-600 hover:!bg-emerald-500 !border-emerald-500 flex items-center justify-center gap-1.5 font-bold"
          >
            <span>Dosto ko bhej 📲</span>
          </a>

          <button
            type="button"
            onClick={handleCopy}
            className="btn-ghost !py-2 !px-3 !text-xs"
          >
            {copied ? '✓ Link Copied!' : 'Copy Link'}
          </button>
        </div>
      </div>
    </div>
  )
}
