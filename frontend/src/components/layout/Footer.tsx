import { IconBrandGithub, IconBrandX } from "@tabler/icons-react";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full py-4 pb-8 sm:pb-4 mt-auto border-t border-border/20 bg-background/50 backdrop-blur-sm z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-col md:flex-row items-center justify-between gap-4 sm:gap-6">
        <div className="flex flex-col items-center md:items-start gap-2">
          <p className="text-xs text-muted-foreground font-medium text-center">
            &copy; {currentYear} BrainLattice. All rights reserved.
          </p>
        </div>

        <div className="flex items-center gap-8">
          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/rickytang666" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-muted-foreground/60 hover:text-foreground transition-colors"
              title="View Author's GitHub"
            >
              <IconBrandGithub className="w-5 h-5" />
            </a>
            <a 
              href="https://x.com/_rickytang" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-muted-foreground/60 hover:text-foreground transition-colors"
              title="Follow Author on X"
            >
              <IconBrandX className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
