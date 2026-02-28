import { NavLink, Routes, Route, useLocation } from "react-router-dom";
import { useState } from "react";
import { SignInButton, UserButton, SignedIn, SignedOut } from "@clerk/clerk-react";
import GraphScratchpad from "./components/scratchpad/GraphScratchpad";
import ProjectDashboard from "./components/dashboard/ProjectDashboard";
import ConfigModal from "./components/dashboard/ConfigModal";
import { Settings } from "lucide-react";
import { ThemeToggle } from "./components/ThemeToggle";
import { useAuthSync } from "./hooks/useAuthSync";
import { Logo } from "./components/Logo";

const LAST_PROJECT_KEY = "brainlattice_last_project";

function getDashboardPath(): string {
  const last = sessionStorage.getItem(LAST_PROJECT_KEY);
  return last ? `/${last}` : "/";
}

function App() {
  useAuthSync();
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const location = useLocation();
  const isDashboard = location.pathname !== "/scratchpad";

  return (
    <div className="w-screen h-screen overflow-hidden antialiased text-foreground bg-background flex flex-col">
      <ConfigModal isOpen={isConfigOpen} onClose={() => setIsConfigOpen(false)} />

      {/* Top Navigation */}
      <div className="flex-none h-12 border-b border-border bg-card px-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Logo className="w-6 h-6 text-primary" />
          <div 
            className="font-bold text-primary text-lg mt-0.5" 
            style={{ fontFamily: '"Space Grotesk", sans-serif' }}
          >
            BrainLattice
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 mr-2">
            <NavLink
              to={getDashboardPath()}
              className={`flex items-center gap-1.5 text-sm font-medium transition-colors ${isDashboard ? "text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/scratchpad"
              className={({ isActive }) =>
                `flex items-center gap-1.5 text-sm font-medium transition-colors ${isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground"}`
              }
            >
              Scratchpad
            </NavLink>
          </div>
          
          <button
            onClick={() => setIsConfigOpen(true)}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
            title="API Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <ThemeToggle />

          <div className="flex items-center border-l border-border pl-4 ml-2">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-3 py-1.5 text-sm font-medium bg-primary hover:bg-primary/80 text-primary-foreground rounded transition-colors">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton appearance={{ elements: { avatarBox: "w-8 h-8 rounded border border-border hover:border-primary transition-colors" } }} />
            </SignedIn>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden relative">
        <Routes>
          <Route path="/scratchpad" element={<GraphScratchpad />} />
          <Route path="/" element={<ProjectDashboard />} />
          <Route path="/:projectId" element={<ProjectDashboard />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
