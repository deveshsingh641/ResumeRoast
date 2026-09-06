
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/react'
import { PageTracker } from '@/components/PageTracker'
import LandingPage from '@/pages/LandingPage'
import RoastPage from '@/pages/RoastPage'
import MatchPage from '@/pages/MatchPage'
import ResultsPage from '@/pages/ResultsPage'
import BattlePage from '@/pages/BattlePage'
import WallPage from '@/pages/WallPage'
import PricingPage from '@/pages/PricingPage'
import PrivacyPage from '@/pages/PrivacyPage'
import TermsPage from '@/pages/TermsPage'
import NotFoundPage from '@/pages/NotFoundPage'
import FounderDashboardPage from '@/pages/FounderDashboardPage'

import SuggestionStickyTrigger from '@/components/SuggestionStickyTrigger'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/roast" element={<RoastPage />} />
        <Route path="/match" element={<MatchPage />} />
        <Route path="/roast/:id" element={<ResultsPage />} />
        <Route path="/battle" element={<BattlePage />} />
        <Route path="/battle/:id" element={<BattlePage />} />
        <Route path="/wall" element={<WallPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/admin/checkout-test" element={<PricingPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/stats" element={<FounderDashboardPage />} />
        <Route path="/admin" element={<FounderDashboardPage />} />
        <Route path="/founder" element={<FounderDashboardPage />} />

        {/* Catch-all 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <SuggestionStickyTrigger />
      <PageTracker />
      <Analytics />
      <SpeedInsights />
    </BrowserRouter>
  )
}
