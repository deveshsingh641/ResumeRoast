import { useState, useEffect } from 'react'

export default function LiveRoastCounter() {
  const [count, setCount] = useState(12847)

  useEffect(() => {
    // Subtle live increment every 12-25 seconds to feel active and authentic
    const interval = setInterval(() => {
      setCount((prev) => prev + Math.floor(Math.random() * 2) + 1)
    }, 14000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="inline-flex items-center gap-2 bg-[#1A1612] border border-amber-500/20 rounded-full px-3.5 py-1 text-xs select-none shadow-sm mb-6">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
      </span>
      <span className="font-mono text-tan-dim tracking-wide">
        <strong className="text-amber-400 font-bold">
          {count.toLocaleString()}
        </strong>{' '}
        resumes ab tak <span className="text-paper font-semibold">bhun chuke hain</span> 🔥
      </span>
    </div>
  )
}
