import { useState, useEffect, useRef, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import KnowledgeGraph from "../graph/KnowledgeGraph";
import NoteSidebar from "./NoteSidebar";
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
} from "lucide-react";

import { API_BASE } from "../../config";

const LAST_PROJECT_KEY = "brainlattice_last_project";

interface Project {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

export default function ProjectDashboard() {
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
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [focusNodeId, setFocusNodeId] = useState<string | null>(null);

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

  const fetchProjects = () => {
    fetch(`${API_BASE}/projects/list`)
      .then((res) => res.json())
      .then((data) => {
        setProjects(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  // persist last viewed project for "Dashboard" nav from scratchpad
  useEffect(() => {
    if (selectedProjectId) {
      sessionStorage.setItem(LAST_PROJECT_KEY, selectedProjectId);
    }
  }, [selectedProjectId]);

  useEffect(() => {
    fetchProjects();
    // Poll every 5s if any project is processing
    const interval = setInterval(() => {
      setProjects((prev) => {
        if (prev.some((p) => p.status === "processing")) {
          fetchProjects();
        }
        return prev;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, []);

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
    fetch(`${API_BASE}/project/${projectIdFromUrl}/graph`)
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
  }, [projectIdFromUrl]);

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
      const res = await fetch(`${API_BASE}/ingest/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        fetchProjects(); // refresh list
      } else {
        console.error("Upload failed");
      }
    } catch (err) {
      console.error(err);
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
      const res = await fetch(
        `${API_BASE}/project/${selectedProjectId}/title`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: newTitle }),
        },
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
      const res = await fetch(`${API_BASE}/project/${id}`, {
        method: "DELETE",
      });
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
    <div className="flex h-full w-full bg-[#0a0a0a] overflow-hidden text-neutral-200 font-sans">
      {/* Homepage: Project List */}
      {!selectedProjectId && (
        <div className="flex flex-col w-full max-w-4xl mx-auto px-6 py-16">
          {/* Hero Section */}
          <div className="text-center mb-16">
            <h1 className="text-4xl font-bold text-neutral-100 mb-3 tracking-tight">
              Your Knowledge Graph
            </h1>
            <p className="text-neutral-400 text-lg max-w-xl mx-auto">
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
              className="w-full max-w-md mx-auto flex items-center justify-center gap-3 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-800 disabled:text-neutral-500 text-white font-semibold py-4 px-6 rounded-xl transition-all text-base shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 disabled:shadow-none"
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
              <Loader2 className="w-8 h-8 animate-spin text-neutral-600" />
            </div>
          ) : projects.length === 0 ? (
            <div className="text-center py-20">
              <Database className="w-12 h-12 text-neutral-700 mx-auto mb-4" />
              <p className="text-neutral-500 text-lg mb-1">No projects yet</p>
              <p className="text-neutral-600 text-sm">Upload your first PDF to create a knowledge graph</p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-neutral-200">
                  Recent Projects
                </h2>
                <button
                  onClick={fetchProjects}
                  className="p-2 text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800 rounded-lg transition-colors"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {projects.map((p) => (
                  <div
                    key={p.id}
                    className="group relative bg-neutral-900/50 border border-neutral-800 rounded-xl p-5 hover:border-neutral-700 hover:bg-neutral-900 transition-all cursor-pointer"
                    onClick={() => selectProject(p.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-semibold text-neutral-100 text-base pr-8 line-clamp-2">
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
                            ? "bg-emerald-500/10 text-emerald-400"
                            : p.status === "failed"
                            ? "bg-red-500/10 text-red-400"
                            : "bg-amber-500/10 text-amber-400"
                        }`}
                      >
                        {p.status}
                      </span>
                      <span className="text-neutral-500 text-xs">
                        {new Date(p.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </span>
                    </div>

                    {deletingId === p.id && (
                      <div className="absolute inset-0 bg-neutral-950/95 backdrop-blur-sm rounded-xl flex items-center justify-center gap-3 z-10 border border-red-500/30">
                        <span className="text-sm font-medium text-red-400">
                          Delete this project?
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteProject(p.id);
                          }}
                          className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm font-medium transition-colors"
                        >
                          Delete
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeletingId(null);
                          }}
                          className="px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg text-sm font-medium transition-colors"
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
            className="min-w-0 h-full flex flex-col relative overflow-hidden bg-[#0a0a0a] shrink-0"
            style={{ width: `${graphWidthPercent}%` }}
          >
            {/* Header overlay - scoped to graph panel only */}
            <div className="absolute top-6 left-6 z-10 flex items-center gap-4">
              <button
                onClick={() => navigate("/")}
                className="p-2 bg-neutral-900 border border-neutral-800 rounded-full hover:bg-neutral-800 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 text-neutral-400" />
              </button>
              <div className="px-4 py-2 bg-neutral-900/80 backdrop-blur-md border border-neutral-800 rounded-full flex items-center gap-3">
                {editingTitle ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      className="bg-neutral-900 border border-neutral-700 rounded px-2 py-0.5 text-xs text-neutral-200 outline-none focus:border-emerald-500 font-sans normal-case"
                      autoFocus
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRename();
                        if (e.key === "Escape") setEditingTitle(false);
                      }}
                    />
                    <button
                      onClick={handleRename}
                      className="text-emerald-500 hover:text-emerald-400"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setEditingTitle(false)}
                      className="text-neutral-500 hover:text-red-400"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <span className="text-xs font-bold text-neutral-300 uppercase tracking-wider">
                      {currentProject?.title}
                    </span>
                    <button
                      onClick={() => {
                        setNewTitle(currentProject?.title || "");
                        setEditingTitle(true);
                      }}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-neutral-500 hover:text-neutral-300"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  </div>
                )}
                {projectGraph && (
                  <>
                    <span className="w-1 h-1 bg-neutral-700 rounded-full" />
                    <span className="text-xs text-emerald-400">
                      {projectGraph.nodes.length} Nodes
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Graph Section - fills panel, explicit bounds for canvas */}
            <div className="flex-1 min-h-0 relative w-full overflow-hidden">
              {graphLoading ? (
                <div className="w-full h-full flex items-center justify-center">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-500/50" />
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
                <div className="w-full h-full flex items-center justify-center text-neutral-600">
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
              className={`h-full w-px transition-colors ${isResizing ? "bg-neutral-500" : "bg-neutral-800 hover:bg-neutral-600"}`}
            />
          </div>

          {/* Note Panel - resizable */}
          <div
            className="min-w-[280px] shrink-0 h-full flex flex-col overflow-hidden border-l border-neutral-800 bg-[#0f0f0f]"
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
