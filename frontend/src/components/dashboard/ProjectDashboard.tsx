import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import KnowledgeGraph from "../graph/KnowledgeGraph";
import NoteSidebar from "./NoteSidebar";
import SearchBar from "./SearchBar";
import type { GraphData } from "../../types/graph";
import {
  Database,
  Loader2,
  ArrowLeft,
  Upload,
  RefreshCw,
  Edit2,
  Check,
  X,
  Trash2,
  FileDown,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@clerk/clerk-react";

import { API_BASE, apiFetch } from "../../config";

const LAST_PROJECT_KEY = "brainlattice_last_project";

interface Project {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

export default function ProjectDashboard() {
  const { userId } = useAuth();
  const { projectId: projectIdFromUrl } = useParams<{ projectId?: string }>();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const selectedProjectId = projectIdFromUrl ?? null;
  const [projectGraph, setProjectGraph] = useState<GraphData | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);

  // Obsidian Export State
  const [exportLoading, setExportLoading] = useState(false);
  const [exportStatus, setExportStatus] = useState<{
    status: string;
    progress: number;
    message: string;
    download_url?: string;
  } | null>(null);
  const exportPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startExportPolling = useCallback(() => {
    if (exportPollRef.current) clearInterval(exportPollRef.current);
    exportPollRef.current = setInterval(async () => {
      try {
        const res = await apiFetch(
          `${API_BASE}/project/${projectIdFromUrl}/export/status`,
          undefined,
          userId
        );
        if (res.ok) {
          const status = await res.json();
          setExportStatus(status);
          if (status.status === "complete" || status.status === "failed") {
            if (exportPollRef.current) clearInterval(exportPollRef.current);
            setExportLoading(false);
          }
        }
      } catch (err) {
        console.error("poll error:", err);
      }
    }, 2000);
  }, [projectIdFromUrl, userId]);

  const handleExport = async () => {
    if (!projectIdFromUrl) return;
    setExportLoading(true);
    setExportStatus({ status: "pending", progress: 0, message: "Exporting..." });

    try {
      const res = await apiFetch(
        `${API_BASE}/project/${projectIdFromUrl}/export/obsidian`,
        { method: "POST" },
        userId
      );
      if (res.ok) {
        startExportPolling();
      } else {
        throw new Error("Failed to trigger export");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to start export.");
      setExportLoading(false);
      setExportStatus(null);
    }
  };

  const handleDownloadVault = async () => {
    if (!projectIdFromUrl) return;
    try {
      const res = await apiFetch(
        `${API_BASE}/project/${projectIdFromUrl}/export/download`,
        undefined,
        userId
      );
      if (res.ok) {
        const { download_url } = await res.json();
        // if local dev, prefix with API_BASE
        const fullUrl = download_url.startsWith("http") ? download_url : `${API_BASE}${download_url}`;
        window.open(fullUrl, "_blank");
      }
    } catch (err) {
      console.error(err);
      setError("Failed to download vault.");
    }
  };

  // Check export status on load
  useEffect(() => {
    if (!projectIdFromUrl) {
      setExportStatus(null);
      return;
    }

    apiFetch(`${API_BASE}/project/${projectIdFromUrl}/export/status`, undefined, userId)
      .then(res => res.json())
      .then(status => {
        if (status && status.status !== "none") {
          setExportStatus(status);
          if (status.status === "pending" || status.status === "generating") {
            setExportLoading(true);
            startExportPolling();
          }
        }
      })
      .catch(err => console.error("Initial export status check failed:", err));
  }, [projectIdFromUrl, userId, startExportPolling]);

  useEffect(() => {
    return () => {
      if (exportPollRef.current) clearInterval(exportPollRef.current);
    };
  }, []);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const panelsContainerRef = useRef<HTMLDivElement>(null);
  const [graphWidthPercent, setGraphWidthPercent] = useState(60);
  const [isResizing, setIsResizing] = useState(false);

  const clearFocusNodeId = useCallback(() => setFocusNodeId(null), []);

  const handleResizeStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;
    const container = panelsContainerRef.current;
    if (!container) return;

    const handleMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = (x / rect.width) * 100;
      const minGraph = 25;
      const maxGraph = Math.max(minGraph, 100 - (280 / rect.width) * 100);
      setGraphWidthPercent(Math.max(minGraph, Math.min(maxGraph, pct)));
    };
    const handleEnd = () => setIsResizing(false);

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("mouseup", handleEnd);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    return () => {
      document.removeEventListener("mousemove", handleMove);
      document.removeEventListener("mouseup", handleEnd);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isResizing]);

  const fetchProjects = useCallback(() => {
    apiFetch(`${API_BASE}/projects/list`, undefined, userId)
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
        setLoading(false);
        
        // redirect if in a project view but it doesn't exist
        if (projectIdFromUrl && !data.find((p: Project) => p.id === projectIdFromUrl)) {
          navigate("/");
        }
        
        // clean up stale last_project if list is empty
        if (data.length === 0) {
          sessionStorage.removeItem(LAST_PROJECT_KEY);
        }
      })
      .catch((err) => {
        console.error(err);
        setError("Failed to fetch projects. Please check your connection.");
        setLoading(false);
      });
  }, [userId, navigate, projectIdFromUrl]);

  // persist last viewed project for "Dashboard" nav from scratchpad
  useEffect(() => {
    if (selectedProjectId) {
      sessionStorage.setItem(LAST_PROJECT_KEY, selectedProjectId);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchProjects();
    // Poll every 2s if any project is processing
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

  // when projectId from URL changes, fetch graph and reset selection
  useEffect(() => {
    setSelectedNodeId(null);
    setFocusNodeId(null);
    if (!projectIdFromUrl) {
      setProjectGraph(null);
      setGraphLoading(false);
      return;
    }
    setGraphLoading(true);
    apiFetch(`${API_BASE}/project/${projectIdFromUrl}/graph`, undefined, userId)
      .then((res) => {
        if (!res.ok) throw new Error(`http error! status: ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setProjectGraph(data);
        setGraphLoading(false);
      })
      .catch((err) => {
        console.error("failed to fetch graph:", err);
        setProjectGraph(null);
        setGraphLoading(false);
      });
  }, [projectIdFromUrl, userId]);

  const selectProject = (id: string) => {
    setSelectedNodeId(null);
    navigate(`/${id}`);
  };

  const currentProject = projects.find((p) => p.id === selectedProjectId);

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
        setError(null);
        fetchProjects(); // refresh list immediately
      } else {
        const data = await res.json().catch(() => ({}));
        if (res.status === 401 || res.status === 403 || (data.detail && data.detail.includes("API key"))) {
          setError("API key is required. Please click the Settings icon and enter your key.");
        } else {
          setError(`Upload failed: ${data.detail || 'Server error'}`);
        }
      }
    } catch (err) {
      console.error(err);
      setError("Network error. Could not connect to the processing engine.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRename = async () => {
    if (
      !selectedProjectId ||
      !newTitle.trim() ||
      newTitle === currentProject?.title
    ) {
      setEditingTitle(false);
      return;
    }

    try {
      const res = await apiFetch(
        `${API_BASE}/project/${selectedProjectId}/title`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle }),
        },
        userId
      );
      if (res.ok) {
        setProjects(
          projects.map((p) =>
            p.id === selectedProjectId ? { ...p, title: newTitle } : p,
          ),
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setEditingTitle(false);
    }
  };

  const handleDeleteProject = async (id: string) => {
    try {
      const res = await apiFetch(`${API_BASE}/project/${id}`, {
        method: "DELETE",
      }, userId);
      if (res.ok) {
        setProjects(projects.filter((p) => p.id !== id));
        if (selectedProjectId === id) {
          navigate("/");
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="flex h-full w-full bg-background overflow-hidden text-foreground font-sans relative">
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[100] w-full max-w-xl px-4 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-4">
            <div className="bg-red-500/20 p-2 rounded-lg">
              <X className="w-5 h-5 text-red-400" />
            </div>
            <div className="flex-1 pt-0.5">
              <h4 className="text-sm font-bold text-red-200 uppercase tracking-tight mb-1">Attention Required</h4>
              <p className="text-sm text-red-300/90 leading-relaxed font-medium">
                {error}
              </p>
            </div>
            <button 
              onClick={() => setError(null)}
              className="p-1 text-red-400/50 hover:text-red-200 hover:bg-red-500/20 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Homepage: Project List */}
      {!selectedProjectId && (
        <div className="flex flex-col w-full max-w-4xl mx-auto px-6 py-16">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <h1 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
              Your Knowledge Graph
            </h1>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">
              Transform PDFs into interactive study notes. Upload a document to get started.
            </p>
          </div>

          {/* Upload Section */}
          <div className="mb-12">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleUpload}
              accept=".pdf"
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="w-full max-w-md mx-auto flex items-center justify-center gap-3 bg-primary hover:bg-primary/80 disabled:bg-muted disabled:opacity-50 disabled:cursor-not-allowed text-primary-foreground font-semibold py-4 px-6 rounded-xl transition-all text-base disabled:shadow-none"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload PDF Document</span>
                </>
              )}
            </button>
          </div>

          {/* Projects List */}
          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-20">
              <Database className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground text-lg mb-1">No projects yet</p>
              <p className="text-muted-foreground/70 text-sm">Upload your first PDF to create a knowledge graph</p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-foreground">
                  Recent Projects
                </h2>
                <button
                  onClick={fetchProjects}
                  className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition-colors"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {projects.map((p) => (
                  <div
                    key={p.id}
                    className="group relative bg-card/50 border border-border rounded-xl p-5 hover:border-border/80 hover:bg-card transition-all cursor-pointer"
                    onClick={() => selectProject(p.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-foreground text-base pr-8 line-clamp-2">
                        {p.title}
                      </h3>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingId(p.id);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1.5 text-neutral-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all shrink-0"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span
                        className={`px-2.5 py-1 rounded-md text-xs font-medium ${
                          p.status === "complete"
                            ? "bg-primary/10 text-primary"
                            : p.status === "failed"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-amber-500/10 text-amber-400"
                        }`}
                      >
                        {p.status}
                      </span>
                      <span className="text-muted-foreground text-xs">
                        {new Date(p.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </span>
                    </div>

                    {deletingId === p.id && (
                      <div className="absolute inset-0 bg-background/95 rounded-xl flex items-center justify-center gap-3 z-10 border border-border/50">
                        <span className="text-sm font-medium text-destructive">
                          Delete this project?
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteProject(p.id);
                          }}
                          className="px-3 py-1.5 bg-destructive/20 hover:bg-destructive/30 text-destructive rounded-lg text-sm font-medium transition-colors"
                        >
                          Delete
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingId(null);
                          }}
                          className="px-3 py-1.5 bg-muted hover:bg-accent hover:text-accent-foreground text-muted-foreground rounded-lg text-sm font-medium transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Main Area: Graph + Note as separate panels */}
      {selectedProjectId && (
        <div
          ref={panelsContainerRef}
          className="flex-1 flex flex-row w-full min-w-0 overflow-hidden relative"
        >
          {/* Graph Panel - resizable */}
          <div
            className="min-w-0 h-full flex flex-col relative overflow-hidden bg-background shrink-0"
            style={{ width: `${graphWidthPercent}%` }}
          >
             {/* Header overlay - scoped to graph panel only */}
            <div className="absolute top-6 left-6 z-10 flex items-center gap-4">
              <button
                onClick={() => navigate("/")}
                className="p-2 bg-card border border-border/50 rounded-full hover:bg-muted transition-colors"
              >
                <ArrowLeft className="w-4 h-4 text-muted-foreground" />
              </button>
              <div className="px-4 py-2 bg-card border border-border/50 rounded-full flex items-center gap-3">
                {editingTitle ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="bg-muted border border-border rounded px-2 py-0.5 text-xs text-foreground outline-none focus:border-primary font-sans normal-case"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRename();
                        if (e.key === "Escape") setEditingTitle(false);
                      }}
                    />
                    <button
                      onClick={handleRename}
                      className="text-primary hover:text-primary/80"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setEditingTitle(false)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <span className="text-xs font-bold text-foreground tracking-wider">
                      {currentProject?.title}
                    </span>
                    <button
                      onClick={() => {
                        setNewTitle(currentProject?.title || "");
                        setEditingTitle(true);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {projectGraph && (
                  <>
                    <span className="w-1 h-1 bg-border rounded-full" />
                    <span className="text-xs text-primary">
                      {projectGraph.nodes.length} Nodes
                    </span>
                    <span className="w-1 h-1 bg-border rounded-full" />
                    
                    {/* Obsidian Export Actions */}
                    <div className="flex items-center gap-2">
                       {exportStatus?.status === "complete" && (
                         <button
                           onClick={handleDownloadVault}
                           className="flex items-center gap-1.5 px-2.5 py-1 bg-primary/20 hover:bg-primary/30 text-primary text-[10px] font-bold uppercase rounded-lg border border-primary/30 transition-all animate-pulse"
                         >
                           <FileDown className="w-3 h-3" />
                           Download .Zip
                         </button>
                       )}
                       
                       <button
                         onClick={handleExport}
                         disabled={exportLoading && (!exportStatus || exportStatus.status === "pending")}
                         className="flex items-center gap-1.5 px-2.5 py-1 bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground text-[10px] font-bold uppercase rounded-lg border border-border transition-all"
                         title={exportStatus?.status === "generating" ? "Click to force retry if stuck" : "Export this graph to Obsidian"}
                       >
                         <Sparkles className={`w-3 h-3 ${exportLoading ? "animate-spin text-primary/80" : "text-primary"}`} />
                         {exportStatus?.status === "generating" 
                           ? `Exporting ${exportStatus.progress || 0}%`
                           : exportStatus?.status === "complete"
                             ? "Update Vault"
                             : exportStatus?.status === "failed"
                               ? "Retry Export"
                               : "Export to Obsidian"}
                       </button>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Graph Section - fills panel, explicit bounds for canvas */}
            <div className="flex-1 min-h-0 relative w-full overflow-hidden">
              {projectGraph && (
                <SearchBar 
                  data={projectGraph} 
                  onSelectNode={(id) => {
                    setSelectedNodeId(id);
                    setFocusNodeId(id);
                  }}
                />
              )}
              {graphLoading ? (
                <div className="w-full h-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-primary/50" />
                </div>
              ) : projectGraph ? (
                <KnowledgeGraph
                  data={projectGraph}
                  onNodeSelect={(id) => {
                    setSelectedNodeId(id);
                    setFocusNodeId(id);
                  }}
                  focusNodeId={focusNodeId}
                  onFocusComplete={clearFocusNodeId}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                  Failed to load graph.
                </div>
              )}
            </div>
          </div>

          {/* Resize handle */}
          <div
            onMouseDown={handleResizeStart}
            className="absolute top-0 bottom-0 w-1.5 cursor-col-resize z-30 shrink-0 select-none flex justify-center"
            style={{ left: `calc(${graphWidthPercent}% - 3px)` }}
            title="Drag to resize"
          >
            <div
              className={`h-full w-px transition-colors ${isResizing ? "bg-muted-foreground" : "bg-border hover:bg-muted-foreground"}`}
            />
          </div>

          {/* Note Panel - resizable */}
          <div
            className="min-w-[280px] shrink-0 h-full flex flex-col overflow-hidden border-l border-border/50 bg-card"
            style={{ width: `${100 - graphWidthPercent}%` }}
          >
            <NoteSidebar
              projectId={selectedProjectId}
              conceptId={selectedNodeId}
              aliases={
                projectGraph?.nodes.find((n) => n.id === selectedNodeId)
                  ?.aliases ?? []
              }
              validNodeIds={
                projectGraph
                  ? new Set(projectGraph.nodes.map((n) => n.id.toLowerCase()))
                  : undefined
              }
              onClose={() => setSelectedNodeId(null)}
              onNodeSelect={(id) => {
                setSelectedNodeId(id);
                setFocusNodeId(id);
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
