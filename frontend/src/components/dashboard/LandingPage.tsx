import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2, Upload, RefreshCw, Trash2, Search } from "lucide-react";
import { useAuth } from "@clerk/clerk-react";
import { API_BASE, apiFetch } from "../../config";

interface Project {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

export default function LandingPage() {
  const { userId } = useAuth();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Cmd+K shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const fetchProjects = useCallback(() => {
    apiFetch(`${API_BASE}/projects/list`, undefined, userId)
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [userId]);

  useEffect(() => {
    fetchProjects();
    const interval = setInterval(() => {
      setProjects((prev) => {
        if (prev.some((p) => p.status === "processing")) {
          fetchProjects();
        }
        return prev;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [fetchProjects]);

  const selectProject = (id: string) => {
    navigate(`/${id}`);
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await apiFetch(`${API_BASE}/ingest/upload`, {
        method: "POST",
        body: formData,
      }, userId);
      
      if (res.ok) {
        fetchProjects();
      } else {
        const data = await res.json().catch(() => ({}));
        if (res.status === 401 || res.status === 403 || (data?.detail && data.detail.includes("API key"))) {
          alert("API key is required. Please click the Settings icon and enter your key.");
        } else {
          alert(`Upload failed: ${data?.detail || 'Server error'}`);
        }
      }
    } catch (err) {
      console.error(err);
      alert("Network error. Could not connect to the processing engine.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      const res = await apiFetch(`${API_BASE}/project/${id}`, {
        method: "DELETE",
      }, userId);
      if (res.ok) {
        setProjects(projects.filter((p) => p.id !== id));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div 
      className="flex flex-col items-center justify-start pt-[25vh] w-full h-full relative overflow-hidden bg-background"
      onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('bg-primary/5'); }}
      onDragLeave={(e) => { e.preventDefault(); e.currentTarget.classList.remove('bg-primary/5'); }}
      onDrop={(e) => {
        e.preventDefault();
        e.currentTarget.classList.remove('bg-primary/5');
        const file = e.dataTransfer.files?.[0];
        if (file && file.type === "application/pdf") {
          const dT = new DataTransfer();
          dT.items.add(file);
          if (fileInputRef.current) {
            fileInputRef.current.files = dT.files;
            handleUpload({ target: { files: dT.files } } as any);
          }
        }
      }}
    >
      {/* Subtle Ambient Background */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.3]" 
           style={{ 
             background: 'radial-gradient(circle at 50% -20%, hsl(var(--primary)/0.15), transparent 60%), radial-gradient(circle at 50% 120%, hsl(var(--primary)/0.05), transparent 50%)' 
           }} 
      />
      <div className="absolute inset-0 pointer-events-none opacity-[0.015]"
           style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, currentColor 1px, transparent 0)', backgroundSize: '48px 48px' }}
      />
      
      <div className="z-10 w-full max-w-2xl px-6 flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-1000">
         {/* The Omnibar */}
         <div className="w-full relative group">
           <div className="absolute -inset-1.5 bg-gradient-to-r from-primary/10 via-primary/5 to-transparent rounded-[24px] blur-lg opacity-0 group-hover:opacity-100 transition duration-1000 group-hover:duration-300" />
           <div className="relative flex items-center w-full bg-card/60 backdrop-blur-2xl border border-border/40 shadow-[0_8px_32px_-8px_rgba(0,0,0,0.1)] rounded-[20px] overflow-hidden focus-within:ring-1 focus-within:ring-primary/20 focus-within:border-primary/30 transition-all duration-500">
              <div className="pl-6 pr-3 text-muted-foreground group-focus-within:text-primary transition-colors duration-500">
                {uploading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Search className="w-5 h-5 opacity-70" />}
              </div>
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    const q = searchQuery.toLowerCase();
                    if (q.includes('upload') || q.includes('new') || q.includes('create')) {
                      fileInputRef.current?.click();
                      setSearchQuery('');
                    }
                  }
                }}
                placeholder="Search past projects, or type 'upload' and hit enter..."
                className="w-full bg-transparent border-none py-4 text-base tracking-wide text-foreground placeholder-muted-foreground/40 focus:outline-none focus:ring-0 font-sans"
                autoFocus
              />
              <div className="pr-4 flex items-center gap-3">
                 <button 
                   onClick={() => fileInputRef.current?.click()}
                   disabled={uploading}
                   className="p-2 rounded-xl bg-primary/5 text-primary/80 hover:text-primary hover:bg-primary/10 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
                   title="Upload PDF"
                 >
                    <Upload className="w-4 h-4" />
                 </button>
                 <div className="h-5 w-px bg-border/40 max-sm:hidden" />
                 <kbd className="hidden sm:inline-flex items-center gap-1 px-2.5 py-1 rounded bg-muted/40 text-xs font-medium tracking-widest text-muted-foreground border border-border/30">
                   <span className="text-base">⌘</span>K
                 </kbd>
              </div>
           </div>
         </div>

         <input
            type="file"
            ref={fileInputRef}
            onChange={handleUpload}
            accept=".pdf"
            className="hidden"
         />

         {/* Recent Projects Minimal List */}
         <div className="w-full max-w-xl mt-10 flex flex-col transition-opacity duration-500">
            <div className="flex items-center justify-between mb-2 px-3">
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground">Recent History</span>
              <button
                onClick={fetchProjects}
                className="p-1 text-muted-foreground/40 hover:text-foreground transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
              </button>
            </div>
            
            {loading ? (
              <div className="py-4 flex flex-col gap-2 px-3">
                <div className="h-8 bg-muted/20 rounded-lg w-full animate-pulse" />
                <div className="h-8 bg-muted/10 rounded-lg w-3/4 animate-pulse" />
              </div>
            ) : projects.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground/30 text-sm font-medium">
                No vectors stored.
              </div>
            ) : (
              <div className="flex flex-col gap-0.5">
                {projects
                  .filter((p) => p.title.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map((p) => (
                  <div
                    key={p.id}
                    className="group relative flex items-center justify-between py-2 px-3 hover:bg-muted/30 rounded-lg transition-all cursor-pointer"
                    onClick={() => selectProject(p.id)}
                  >
                    <div className="flex items-center gap-4 overflow-hidden pr-4 w-full">
                      <span className="text-muted-foreground/60 text-[11px] w-12 shrink-0 tabular-nums">
                        {new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                      </span>
                      <h3 className="font-medium text-sm text-foreground/70 group-hover:text-foreground transition-colors truncate">
                        {p.title}
                      </h3>
                    </div>
                    
                    <div className="flex items-center gap-4 opacity-0 group-hover:opacity-100 transition-opacity">
                       {p.status !== "complete" && (
                          <span className={`text-[9px] uppercase font-bold tracking-widest ${p.status === "failed" ? "text-destructive" : "text-amber-500/80"}`}>
                            {p.status}
                          </span>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingId(p.id);
                          }}
                          className="text-muted-foreground/40 hover:text-destructive transition-colors shrink-0"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                    </div>
                    
                    {/* Inline Delete Confirmation */}
                    {deletingId === p.id && (
                      <div className="absolute inset-0 bg-card/95 backdrop-blur-sm flex items-center justify-end gap-4 z-10 px-4 rounded-lg border border-border/20">
                        <span className="text-xs font-medium text-muted-foreground">Delete forever?</span>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeletingId(null);
                            }}
                            className="text-xs px-2 py-1 text-muted-foreground hover:text-foreground font-medium transition-colors"
                          >
                            Cancel
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteProject(p.id);
                            }}
                            className="text-xs px-2 py-1 bg-destructive/10 text-destructive hover:bg-destructive hover:text-destructive-foreground rounded font-semibold transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
         </div>
      </div>
    </div>
  );
}
