import { create } from 'zustand'

export type UploadStatus = 'idle' | 'uploading' | 'analyzing' | 'done' | 'error'
export type ScoreBand = 'weak' | 'mid' | 'strong'

export interface Issue {
  quoted_text: string
  category: string
  roast: string
  fix: string
  start_offset: number | null
  end_offset: number | null
  severity_rank: number | null
}

export interface RoastResult {
  id: string
  overall_score: number
  band: ScoreBand
  one_line_verdict: string
  issues: Issue[]
  total_issues: number
  strengths: string[]
  is_truncated: boolean
  created_at?: string
}

export interface UsageInfo {
  used: number
  remaining: number
  limit: number
  is_pro: boolean
}

interface AppState {
  uploadStatus: UploadStatus
  uploadError: string | null
  result: RoastResult | null
  usage: UsageInfo | null

  setUploadStatus: (status: UploadStatus) => void
  setUploadError: (error: string | null) => void
  setResult: (result: RoastResult | null) => void
  setUsage: (usage: UsageInfo) => void
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  uploadStatus: 'idle',
  uploadError: null,
  result: null,
  usage: null,

  setUploadStatus: (status) => set({ uploadStatus: status }),
  setUploadError: (error) => set({ uploadError: error }),
  setResult: (result) => set({ result }),
  setUsage: (usage) => set({ usage }),
  reset: () =>
    set({ uploadStatus: 'idle', uploadError: null, result: null }),
}))
