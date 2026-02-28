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

      {/* Top Navigation - Floating variant */}
      <div 
        className={`absolute top-0 left-0 right-0 z-50 h-[60px] px-6 flex items-center justify-between transition-colors duration-300 ${
          isDashboard && !location.pathname.slice(1) 
            ? "bg-transparent border-transparent" 
            : "bg-background/80 backdrop-blur-md border-b border-border/50"
        }`}
      >
        <div className="flex items-center gap-2">
          <Logo className="w-5 h-5 text-primary" />
          <div 
              className="font-bold text-primary text-base mt-0.5" 
              style={{ fontFamily: '"Space Grotesk", sans-serif' }}
            >
            BrainLattice
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 mr-2">
            <NavLink
              to={getDashboardPath()}
              className={`flex items-center gap-1.5 text-[13px] font-medium transition-colors ${isDashboard ? "text-foreground" : "text-muted-foreground hover:text-foreground"}`}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/scratchpad"
              className={({ isActive }) =>
                `flex items-center gap-1.5 text-[13px] font-medium transition-colors ${isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground"}`
              }
            >
              Scratchpad
            </NavLink>
          </div>
          
          <button
            onClick={() => setIsConfigOpen(true)}
            className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-md transition-colors"
            title="API Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <ThemeToggle />

          <div className="flex items-center border-l border-border/50 pl-4 ml-2">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-3 py-1.5 text-[13px] font-medium bg-primary hover:bg-primary/90 text-primary-foreground rounded transition-colors shadow-sm">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton appearance={{ elements: { avatarBox: "w-7 h-7 rounded border border-border/50 hover:border-primary/50 transition-colors" } }} />
            </SignedIn>
          </div>
        </div>
      </div>

      {/* Main Content - No top padding needed as children will handle it or sit behind it */}
      <div className="flex-1 w-full h-full relative">
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
