import { Routes, Route, useLocation } from "react-router-dom";
import { useState } from "react";
import { Analytics } from '@vercel/analytics/react';
import GraphScratchpad from "./components/scratchpad/GraphScratchpad";
import ProjectDashboard from "./components/dashboard/ProjectDashboard";
import LandingPage from "./components/dashboard/LandingPage";
import ConfigModal from "./components/dashboard/ConfigModal";
import CliAuthRoute from "./components/dashboard/CliAuthRoute";
import { useAuthSync } from "./hooks/useAuthSync";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { useEffect } from "react";
import { GEMINI_KEY_STORAGE, OPENROUTER_KEY_STORAGE } from "./config";


function App() {
  useAuthSync();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [hasRequiredKeys, setHasRequiredKeys] = useState(true);
  const location = useLocation();
  const isLanding = location.pathname === "/";

  useEffect(() => {
    const geminiKey = localStorage.getItem(GEMINI_KEY_STORAGE);
    const openRouterKey = localStorage.getItem(OPENROUTER_KEY_STORAGE);
    setHasRequiredKeys(!!geminiKey && !!openRouterKey);
  }, [isConfigOpen]);

  return (
    <div className={`w-screen antialiased text-foreground bg-background flex flex-col ${isLanding ? "min-h-screen" : "h-screen overflow-hidden"}`}>
      <ConfigModal isOpen={isConfigOpen} onClose={() => setIsConfigOpen(false)} />
      
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
