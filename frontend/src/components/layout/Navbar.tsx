import { NavLink, useLocation } from "react-router-dom";
import { SignInButton, UserButton, SignedIn, SignedOut } from "@clerk/clerk-react";
import { IconSettings, IconStar, IconKey } from "@tabler/icons-react";
import { FaGithub } from "react-icons/fa";
import { ThemeToggle } from "../ThemeToggle";
import { Logo } from "../Logo";

interface NavbarProps {
  onOpenConfig: () => void;
  hasRequiredKeys: boolean;
}

export function Navbar({ onOpenConfig, hasRequiredKeys }: NavbarProps) {
  const location = useLocation();
  const isDashboard = location.pathname !== "/scratchpad";
  const isLanding = location.pathname === "/";

  return (
    <div 
      className={`absolute top-0 left-0 right-0 z-50 h-[60px] px-4 sm:px-6 flex items-center justify-between transition-colors duration-300 ${
        isDashboard && isLanding 
          ? "bg-transparent border-transparent" 
          : "bg-background/80 backdrop-blur-md border-b border-border/50"
      }`}
    >
      <a href="/">
        <div className="flex items-center gap-2">
          <Logo className="w-5 h-5 text-primary" />
          <div 
            className="font-bold text-primary text-base mt-0.5 hidden sm:block" 
            style={{ fontFamily: '"Space Grotesk", sans-serif' }}
          >
            BrainLattice
          </div>
        </div>
      </a>
      
      <div className="flex items-center gap-1 sm:gap-2">
        <a 
          href="https://github.com/rickytang666/brainlattice" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 p-1.5 sm:px-3 sm:py-1.5 rounded-full border border-border/50 bg-muted/30 text-muted-foreground hover:text-foreground hover:border-border transition-all group"
          title="Star on GitHub"
        >
          <FaGithub className="w-5 h-5 shrink-0" />
          <span className="text-[11px] font-semibold tracking-wide hidden sm:block">Star us on GitHub!</span>
          <IconStar className="w-4 h-4 group-hover:fill-yellow-500/40 group-hover:text-yellow-500 transition-colors hidden sm:block shrink-0" />
        </a>

        <ThemeToggle />
        
        <button
          data-spotlight="key-button"
          onClick={onOpenConfig}
          className={`p-1.5 rounded-md transition-all duration-500 ${
            hasRequiredKeys 
              ? "text-muted-foreground hover:text-foreground" 
              : "text-amber-500 animate-pulse"
          }`}
          title={hasRequiredKeys ? "api keys set" : "missing api keys (gemini + openrouter)"}
        >
          {hasRequiredKeys ? (
            <IconSettings className="w-5 h-5" />
          ) : (
            <IconKey className="w-5 h-5" />
          )}
        </button>

        <NavLink
          to="/scratchpad"
          className={({ isActive }) =>
            `text-[11px] font-medium tracking-wide uppercase transition-colors ${isActive ? "text-primary/70" : "text-muted-foreground/60 hover:text-muted-foreground"}`
          }
          title="Open Graph Scratchpad"
        >
          Scratchpad
        </NavLink>

        {import.meta.env.VITE_CLERK_PUBLISHABLE_KEY && (
          <div className="flex items-center border-l border-border/50 pl-2 ml-1 sm:pl-4 sm:ml-2">
            <SignedOut>
              <SignInButton mode="modal">
                <button className="px-4 py-1.5 text-xs font-semibold text-muted-foreground hover:text-foreground border border-border/50 hover:border-border hover:bg-muted/30 rounded-full transition-all tracking-wide">
                  Sign In
                </button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <UserButton appearance={{ elements: { avatarBox: "w-7 h-7 rounded border border-border/50 hover:border-primary/50 transition-colors" } }} />
            </SignedIn>
          </div>
        )}
      </div>
    </div>
  );
}
