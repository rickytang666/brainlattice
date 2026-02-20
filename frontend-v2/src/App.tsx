import { NavLink, Routes, Route, useLocation } from "react-router-dom";
import GraphScratchpad from "./components/scratchpad/GraphScratchpad";
import ProjectDashboard from "./components/dashboard/ProjectDashboard";
import { LayoutDashboard, TestTube } from "lucide-react";

const LAST_PROJECT_KEY = "brainlattice_last_project";

export function getDashboardPath(): string {
  const last = sessionStorage.getItem(LAST_PROJECT_KEY);
  return last ? `/${last}` : "/";
}

function App() {
  const location = useLocation();
  const isDashboard = location.pathname !== "/scratchpad";

  return (
    <div className="w-screen h-screen overflow-hidden antialiased text-neutral-200 bg-[#0a0a0a] flex flex-col">
      {/* Top Navigation */}
      <div className="flex-none h-12 border-b border-neutral-800 bg-[#0f0f0f] px-4 flex items-center justify-between">
        <div className="font-bold tracking-widest uppercase text-emerald-500 text-sm">
          BrainLattice
        </div>
        <div className="flex items-center gap-2 bg-neutral-900 border border-neutral-800 rounded-lg p-1">
          <NavLink
            to={getDashboardPath()}
            className={`flex items-center gap-2 px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-colors ${isDashboard ? "bg-emerald-500/10 text-emerald-400" : "text-neutral-500 hover:text-neutral-300"}`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            Dashboard
          </NavLink>
          <NavLink
            to="/scratchpad"
            className={({ isActive }) =>
              `flex items-center gap-2 px-3 py-1 rounded text-xs font-semibold uppercase tracking-wider transition-colors ${isActive ? "bg-blue-500/10 text-blue-400" : "text-neutral-500 hover:text-neutral-300"}`
            }
          >
            <TestTube className="w-3.5 h-3.5" />
            Scratchpad
          </NavLink>
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
