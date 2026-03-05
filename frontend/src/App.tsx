import { Routes, Route, useLocation } from "react-router-dom";
import { useState, useCallback } from "react";
import { Analytics } from '@vercel/analytics/react';
import GraphScratchpad from "./components/scratchpad/GraphScratchpad";
import ProjectDashboard from "./components/dashboard/ProjectDashboard";
import LandingPage from "./components/dashboard/LandingPage";
import ConfigModal from "./components/dashboard/ConfigModal";
import CliAuthRoute from "./components/dashboard/CliAuthRoute";
import { useAuthSync } from "./hooks/useAuthSync";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { GEMINI_KEY_STORAGE, OPENROUTER_KEY_STORAGE, shouldShowSpotlight } from "./config";
import { KeysSpotlight } from "./components/KeysSpotlight";

function checkRequiredKeys() {
  const g = localStorage.getItem(GEMINI_KEY_STORAGE);
  const o = localStorage.getItem(OPENROUTER_KEY_STORAGE);
  return !!g && !!o;
}

function App() {
  useAuthSync();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [hasRequiredKeys, setHasRequiredKeys] = useState(checkRequiredKeys);
  const [showSpotlight, setShowSpotlight] = useState(() => !checkRequiredKeys() && shouldShowSpotlight());
  const location = useLocation();
  const isLanding = location.pathname === "/";

  const refreshKeys = useCallback(() => {
    setHasRequiredKeys(checkRequiredKeys());
    setShowSpotlight(false);
  }, []);

  const handleClose = useCallback(() => setIsConfigOpen(false), []);

  return (
    <div className={`w-screen antialiased text-foreground bg-background flex flex-col ${isLanding ? "min-h-screen" : "h-screen overflow-hidden"}`}>
      <ConfigModal isOpen={isConfigOpen} onClose={handleClose} onConfigSaved={refreshKeys} />
      {showSpotlight && (
        <KeysSpotlight
          targetSelector="[data-spotlight='key-button']"
          onDismiss={() => setShowSpotlight(false)}
        />
      )}
      
      <Navbar onOpenConfig={() => setIsConfigOpen(true)} hasRequiredKeys={hasRequiredKeys} />

      <main className="flex-1 w-full relative">
        <Routes>
          <Route path="/scratchpad" element={<GraphScratchpad />} />
          <Route path="/cli-auth" element={<CliAuthRoute />} />
          <Route path="/" element={<LandingPage />} />
          <Route path="/:projectId" element={<ProjectDashboard />} />
        </Routes>
      </main>

      {isLanding && <Footer />}
      <Analytics />
    </div>
  );
}

export default App;
