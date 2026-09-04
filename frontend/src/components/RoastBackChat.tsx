import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

interface Message {
  id: string
  sender: 'ai' | 'user'
  text: string
  timestamp: string
}

interface RoastBackChatProps {
  roastId: string
  overallScore: number
  verdict: string
}

export default function RoastBackChat({ roastId, overallScore, verdict }: RoastBackChatProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'init-1',
      sender: 'ai',
      text: `Score ${overallScore}/100 dekh kar bura laga? "${verdict}" — agar lagta hai tera resume FAANG level tha toh defend kar le khud ko. Bol kya bolna hai? 😈🔥`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    if (isOpen) {
      scrollToBottom()
    }
  }, [messages, isOpen])

  const quickPills = [
    'Ab aur kya badlu isme?',
    'Maine sach mein 40% optimize kiya tha!',
    'Mai aur score badhane ki koshish karunga',
    'Ye buzzword nahi industry standard hai!',
  ]

  const handleSend = async (textToSend?: string) => {
    const msg = (textToSend ?? input).trim()
    if (!msg || loading) return

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: msg,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const historyPayload = messages.slice(-8).map((m) => ({ sender: m.sender, text: m.text }))
      const { data } = await axios.post(`/api/roast/${roastId}/comeback`, {
        message: msg,
        history: historyPayload,
      })
      const aiReply: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: data.reply || 'Defense accha tha bhai, par score fir bhi wahi rahega 💀',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, aiReply])
    } catch {
      const fallbackReply: Message = {
        id: `ai-${Date.now()}`,
        sender: 'ai',
        text: 'Bhai itna bura defense tha ki server bhi crash hone laga! Resume fix karo, debate nahi 😂📉',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }
      setMessages((prev) => [...prev, fallbackReply])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-[640px] mx-auto text-left border border-white/[0.08] bg-[#14110E] rounded-lg overflow-hidden shadow-xl transition-all">
      {/* Header Toggle */}
      <button
        type="button"
        onClick={() => setIsOpen((v) => !v)}
        className="w-full p-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🥊</span>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-display text-base text-paper font-bold">
                Roast Back // Argue with AI
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                LIVE DEBATE
              </span>
            </div>
            <p className="font-mono text-xs text-tan-dim mt-0.5">
              Lagta hai score galat mila? AI roaster se seedha behas karo
            </p>
          </div>
        </div>
        <span className="text-tan-dim font-mono text-xs px-2.5 py-1 bg-white/[0.04] rounded">
          {isOpen ? 'Minimize ▴' : 'Argue Now ▾'}
        </span>
      </button>

      {/* Expandable Chat Body */}
      {isOpen && (
        <div className="border-t border-white/[0.08] p-4 bg-black/30">
          {/* Messages Feed */}
          <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 text-xs leading-relaxed ${
                    m.sender === 'user'
                      ? 'bg-amber-500/15 border border-amber-500/30 text-paper rounded-br-none font-mono'
                      : 'bg-[#1C1814] border border-stamp/30 text-stone-200 rounded-bl-none font-body shadow'
                  }`}
                >
                  <p>{m.text}</p>
                  <span
                    className={`block text-[9px] font-mono mt-1 ${
                      m.sender === 'user' ? 'text-amber-400/60 text-right' : 'text-stone-500'
                    }`}
                  >
                    {m.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs font-mono text-tan-dim py-1">
                <span className="animate-spin text-sm">🔥</span>
                <span>AI roaster cooking comeback…</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Retort Chips */}
          <div className="flex flex-wrap gap-1.5 my-3 pt-2 border-t border-white/[0.06]">
            {quickPills.map((pill, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSend(pill)}
                disabled={loading}
                className="text-[11px] font-mono bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-tan-dim hover:text-paper rounded-full px-2.5 py-1 transition-all"
              >
                {pill}
              </button>
            ))}
          </div>

          {/* Input Row */}
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleSend()
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Apne resume ka bachav karo..."
              disabled={loading}
              className="flex-1 bg-white/[0.05] border border-white/[0.12] rounded px-3 py-2 text-xs font-mono text-paper placeholder:text-stone-500 focus:outline-none focus:border-amber-400"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="btn-primary !text-xs !py-2 !px-4 !bg-red-600 hover:!bg-red-500 font-bold font-mono shrink-0 disabled:opacity-50"
            >
              Reply 🥊
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
