import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { PageTracker } from '@/components/PageTracker'
import LandingPage from '@/pages/LandingPage'
import RoastPage from '@/pages/RoastPage'
import ResultsPage from '@/pages/ResultsPage'
import BattlePage from '@/pages/BattlePage'
import WallPage from '@/pages/WallPage'
import PricingPage from '@/pages/PricingPage'
import PrivacyPage from '@/pages/PrivacyPage'
import TermsPage from '@/pages/TermsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/roast" element={<RoastPage />} />
        <Route path="/roast/:id" element={<ResultsPage />} />
        <Route path="/battle" element={<BattlePage />} />
        <Route path="/battle/:id" element={<BattlePage />} />
        <Route path="/wall" element={<WallPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />

        {/* Catch-all 404 */}
        <Route
          path="*"
          element={
            <main className="min-h-screen flex flex-col items-center justify-center text-center px-4">
              <p className="font-display text-5xl text-stamp mb-4">404</p>
              <p className="font-mono text-tan text-sm mb-6">
                This page doesn't exist. Your career doesn't have to share its fate.
              </p>
              <a href="/" className="btn-primary">
                Back to Resume Roast
              </a>
            </main>
          }
        />
      </Routes>
      <PageTracker />
      <Analytics />
      <SpeedInsights />
    </BrowserRouter>
  )
}
