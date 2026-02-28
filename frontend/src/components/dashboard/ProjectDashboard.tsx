import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import KnowledgeGraph from "../graph/KnowledgeGraph";
import NoteSidebar from "./NoteSidebar";
import SearchBar from "./SearchBar";
import type { GraphData } from "../../types/graph";
import {
  Loader2,
  ArrowLeft,
  Edit2,
  Check,
  X,
  FileDown,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@clerk/clerk-react";

import { API_BASE, apiFetch } from "../../config";


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

  const selectedProjectId = projectIdFromUrl ?? null;
  const [projectGraph, setProjectGraph] = useState<GraphData | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);

  // Project data for the header title
  const [currentProject, setCurrentProject] = useState<Project | null>(null);

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

  // fetch single project info for title
  useEffect(() => {
    if (!projectIdFromUrl) return;
    apiFetch(`${API_BASE}/projects/list`, undefined, userId)
      .then((res) => res.json())
      .then((data) => {
        const p = data.find((x: Project) => x.id === projectIdFromUrl);
        if (p) {
          setCurrentProject(p);
        } else {
          navigate("/");
        }
      })
      .catch((err) => console.error(err));
  }, [userId, navigate, projectIdFromUrl]);

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
        if (currentProject) {
          setCurrentProject({ ...currentProject, title: newTitle });
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setEditingTitle(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-background overflow-hidden text-foreground font-sans relative pt-[60px]">
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-[100] w-full max-w-xl px-4 animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-4">
            <div className="bg-red-500/20 p-2 rounded-lg">
              <X className="w-5 h-5 text-red-400" />
            </div>
            <div className="flex-1 pt-0.5">
              <h4 className="text-sm font-semibold text-red-200 mb-1">Attention Required</h4>
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
            <div className="absolute top-4 left-4 z-10 flex flex-wrap items-center gap-2">
              <button
                onClick={() => navigate("/")}
                className="shrink-0 p-2 bg-card border border-border/50 shadow-sm rounded-full hover:bg-muted transition-colors"
                title="Back to Dashboard"
              >
                <ArrowLeft className="w-4 h-4 text-muted-foreground" />
              </button>
              
              <div className="shrink-0 px-3 py-1.5 bg-card border border-border/50 shadow-sm rounded-full flex items-center gap-2">
                {editingTitle ? (
                  <div className="flex items-center gap-1.5">
                    <input
                      type="text"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="w-32 bg-muted border border-border rounded px-2 py-0.5 text-xs text-foreground outline-none focus:border-foreground font-sans normal-case"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRename();
                        if (e.key === "Escape") setEditingTitle(false);
                      }}
                    />
                    <button
                      onClick={handleRename}
                      className="text-foreground hover:text-muted-foreground"
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
                    <span className="text-xs font-semibold text-foreground tracking-wide">
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
              </div>

              {projectGraph && (
                <>
                  <div className="shrink-0 px-3 py-1 bg-card border border-border/50 shadow-sm rounded-full flex items-center gap-3">
                    <span className="text-[11px] font-medium text-muted-foreground">
                      {projectGraph.nodes.length} nodes
                    </span>
                    
                    {/* Obsidian Export Actions */}
                    <div className="flex items-center gap-1.5 pl-3 border-l border-border/50">
                      {exportStatus?.status === "complete" && (
                        <button
                          onClick={handleDownloadVault}
                          className="flex items-center gap-1.5 px-2.5 py-1 bg-muted hover:bg-muted/80 text-foreground text-[11px] font-medium rounded-md border border-border/50 transition-all"
                        >
                          <FileDown className="w-3 h-3" />
                          download
                        </button>
                      )}
                      
                      <button
                        onClick={handleExport}
                        disabled={exportLoading && (!exportStatus || exportStatus.status === "pending")}
                        className="flex items-center gap-1.5 px-2.5 py-1 bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground text-[11px] font-medium rounded-md border border-border transition-all"
                        title={exportStatus?.status === "generating" ? "Click to force retry if stuck" : "Export this graph to Obsidian"}
                      >
                        <Sparkles className={`w-3 h-3 ${exportLoading ? "animate-spin text-muted-foreground" : "text-foreground"}`} />
                        {exportStatus?.status === "generating" 
                          ? `exporting ${exportStatus.progress || 0}%`
                          : exportStatus?.status === "complete"
                            ? "update"
                            : exportStatus?.status === "failed"
                              ? "retry"
                              : "export"}
                      </button>
                    </div>
                  </div>
                  
                  {/* Search Bar */}
                  <div className="shrink-0">
                    <SearchBar 
                      data={projectGraph} 
                      onSelectNode={(id) => {
                        setSelectedNodeId(id);
                        setFocusNodeId(id);
                      }}
                    />
                  </div>
                </>
              )}
            </div>

             {/* Graph Section - fills panel, explicit bounds for canvas */}
             <div className="flex-1 min-h-0 relative w-full overflow-hidden">
               {graphLoading ? (
                <div className="w-full h-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
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
