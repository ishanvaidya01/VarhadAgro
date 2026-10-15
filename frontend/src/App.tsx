import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Footer } from './components/Footer';

import { RiskMapPage } from './pages/RiskMapPage';
import { DistrictDetailPage } from './pages/DistrictDetailPage';
import { SeasonTrackerPage } from './pages/SeasonTrackerPage';
import { ScenarioLabPage } from './pages/ScenarioLabPage';
import { ReliabilityPage } from './pages/ReliabilityPage';
import { AnalogsPage } from './pages/AnalogsPage';
import { EvidencePage } from './pages/EvidencePage';
import { Privacy } from './pages/Privacy';
import { Terms } from './pages/Terms';
import { NotFound } from './pages/NotFound';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-[#F3EFE6] text-[#1B1A17] font-sans antialiased">
        <Navigation />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
          <Routes>
            <Route path="/" element={<RiskMapPage />} />
            <Route path="/district" element={<DistrictDetailPage />} />
            <Route path="/early-warning" element={<SeasonTrackerPage />} />
            <Route path="/scenario" element={<ScenarioLabPage />} />
            <Route path="/reliability" element={<ReliabilityPage />} />
            <Route path="/analogs" element={<AnalogsPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        <Footer />
      </div>
    </Router>
  );
}
