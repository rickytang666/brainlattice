import { useEffect } from "react";
import { Command } from "cmdk";
import { 
  IconArrowLeft, 
  IconPencil, 
  IconDownload, 
  IconSearch
} from "@tabler/icons-react";
import { ObsidianLogo } from "../Logo";

interface ProjectCommandPaletteProps {
  open: boolean;
  setOpen: (open: boolean) => void;
  onHome: () => void;
  onRename: () => void;
  onExport: () => void;
  onDownload: () => void;
  exportStatus: any;
  exportLoading: boolean;
}

export function ProjectCommandPalette({
  open,
  setOpen,
  onHome,
  onRename,
  onExport,
  onDownload,
  exportStatus,
  exportLoading
}: ProjectCommandPaletteProps) {
  // toggle state of the menu
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen(!open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, setOpen]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      {/* backdrop */}
      <div 
        className="absolute inset-0 bg-background/50 backdrop-blur-sm"
        onClick={() => setOpen(false)}
      />
      
      {/* command palette */}
      <div className="relative w-full max-w-lg overflow-hidden rounded-xl border border-border shadow-2xl bg-popover animate-in fade-in zoom-in-95 duration-200">
        <Command label="Command Menu" className="w-full flex flex-col">
          <Command.Input 
            autoFocus 
            placeholder="type a command or search..." 
            className="w-full px-4 py-4 text-base bg-transparent border-b border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-0"
          />
          <Command.List className="max-h-[300px] overflow-y-auto p-2 scrollbar-thin">
            <Command.Empty className="p-6 text-center text-sm text-muted-foreground">
              no results found :(
            </Command.Empty>

            <Command.Group heading="navigation" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground">
              <Command.Item 
                onSelect={() => { onHome(); setOpen(false); }}
                className="flex items-center gap-2 px-2 py-2 text-sm rounded-md cursor-pointer text-foreground aria-selected:bg-muted aria-selected:text-foreground transition-colors"
                value="home back dashboard return"
              >
                <IconArrowLeft className="w-4 h-4 text-muted-foreground" />
                <span>back to home</span>
              </Command.Item>
              
              <Command.Item 
                onSelect={() => { 
                  setOpen(false); 
                  // Slight delay to allow palette to close before focusing another input
                  setTimeout(() => {
                    const searchInput = document.querySelector('input[placeholder="search graph..."]') as HTMLInputElement;
                    searchInput?.focus();
                  }, 50);
                }}
                className="flex items-center gap-2 px-2 py-2 text-sm rounded-md cursor-pointer text-foreground aria-selected:bg-muted aria-selected:text-foreground transition-colors"
                value="search find node focus"
              >
                <IconSearch className="w-4 h-4 text-muted-foreground" />
                <span>search graph nodes</span>
              </Command.Item>
            </Command.Group>

            <Command.Group heading="project actions" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground mt-2">
              <Command.Item 
                onSelect={() => { onRename(); setOpen(false); }}
                className="flex items-center gap-2 px-2 py-2 text-sm rounded-md cursor-pointer text-foreground aria-selected:bg-muted aria-selected:text-foreground transition-colors"
                value="rename edit title"
              >
                <IconPencil className="w-4 h-4 text-muted-foreground" />
                <span>rename project</span>
              </Command.Item>
            </Command.Group>

            <Command.Group heading="integrations" className="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground mt-2">
              <Command.Item 
                onSelect={() => { 
                  if (!exportLoading && exportStatus?.status !== "generating") {
                    onExport(); 
                    setOpen(false); 
                  }
                }}
                disabled={exportLoading || exportStatus?.status === "generating"}
                className={`flex items-center gap-2 px-2 py-2 text-sm rounded-md cursor-pointer transition-colors ${
                  exportLoading || exportStatus?.status === "generating" 
                  ? "opacity-50 pointer-events-none text-muted-foreground" 
                  : "text-foreground aria-selected:bg-muted aria-selected:text-obsidian"
                }`}
                value="export obsidian sync vault update trigger"
              >
                <ObsidianLogo className="w-4 h-4" />
                <span>
                 {(exportStatus?.status === "generating" || exportStatus?.status === "pending")
                    ? (exportStatus?.download_url ? "updating vault..." : `generating vault (${exportStatus?.progress || 0}%)`)
                    : exportStatus?.status === "complete"
                      ? "update obsidian vault"
                      : "export to obsidian"}
                </span>
                
              </Command.Item>

              {exportStatus?.download_url && (
                <Command.Item 
                  onSelect={() => { onDownload(); setOpen(false); }}
                  className="flex items-center gap-2 px-2 py-2 text-sm rounded-md cursor-pointer text-foreground aria-selected:bg-muted aria-selected:text-foreground transition-colors"
                  value="download zip save local"
                >
                  <IconDownload className="w-4 h-4 text-muted-foreground" />
                  <span>download obsidian vault (.zip)</span>
                </Command.Item>
              )}
            </Command.Group>
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
