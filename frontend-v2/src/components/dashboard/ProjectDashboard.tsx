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
  const clearFocusNodeId = useCallback(() => setFocusNodeId(null), []);

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
      {/* Sidebar: Project List (Hidden when project selected) */}
      {!selectedProjectId && (
        <div className="flex flex-col w-full max-w-md mx-auto my-12 rounded-xl border border-neutral-800 shadow-2xl h-[calc(100vh-6rem)] bg-[#0f0f0f] transition-all duration-300">
          <div className="p-6 border-b border-neutral-800 bg-[#141414] flex justify-between items-start">
            <div>
              <div className="flex items-center gap-3 text-emerald-500 mb-2">
                <Database className="w-6 h-6" />
                <h2 className="font-bold uppercase tracking-widest text-lg text-emerald-400">
                  Knowledge Core
                </h2>
              </div>
              <p className="text-xs text-neutral-500 uppercase tracking-wider">
                Live Ingestion Dashboard
              </p>
            </div>
            <button
              onClick={fetchProjects}
              className="p-1.5 text-neutral-500 hover:text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors"
              title="Refresh List"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {loading ? (
              <div className="flex justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-neutral-600" />
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center p-8 text-neutral-600 text-sm">
                No projects found in database.
              </div>
            ) : (
              projects.map((p) => (
                <div key={p.id} className="group relative">
                  <button
                    onClick={() => selectProject(p.id)}
                    className="w-full text-left p-4 rounded-lg border bg-[#141414] border-neutral-800 hover:border-neutral-600 hover:bg-neutral-900 transition-all"
                  >
                    <div className="font-medium text-sm text-neutral-300 mb-1 truncate pr-8">
                      {p.title}
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span
                        className={`px-2 py-0.5 rounded-full ${p.status === "complete" ? "bg-emerald-500/10 text-emerald-400" : p.status === "failed" ? "bg-red-500/10 text-red-400" : "bg-amber-500/10 text-amber-400"}`}
                      >
                        {p.status}
                      </span>
                      <span className="text-neutral-600">
                        {new Date(p.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </button>

                  {deletingId === p.id ? (
                    <div className="absolute inset-0 bg-neutral-900/90 backdrop-blur-sm rounded-lg flex items-center justify-center gap-2 z-10 border border-red-500/50">
                      <span className="text-[10px] font-bold text-red-400 uppercase tracking-tighter">
                        Delete?
                      </span>
                      <button
                        onClick={() => handleDeleteProject(p.id)}
                        className="p-1 bg-red-500/20 hover:bg-red-500/40 text-red-400 rounded"
                      >
                        <Check className="w-3 h-3" />
                      </button>
                      <button
                        onClick={() => setDeletingId(null)}
                        className="p-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-400 rounded"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeletingId(p.id);
                      }}
                      className="absolute top-4 right-3 opacity-0 group-hover:opacity-100 p-1.5 text-neutral-600 hover:text-red-400 hover:bg-red-500/10 rounded transition-all z-10"
                      title="Delete Project"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t border-neutral-800 bg-[#141414]">
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
              className="w-full flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-neutral-800 disabled:text-neutral-500 text-white font-bold py-2.5 rounded-lg transition-colors text-sm uppercase tracking-wider"
            >
              {uploading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Upload className="w-4 h-4" />
              )}
              {uploading ? "Uploading..." : "Upload Document"}
            </button>
          </div>
        </div>
      )}

      {/* Main Area: Graph + Note as separate panels */}
      {selectedProjectId && (
        <div className="flex-1 flex flex-row w-full min-w-0 overflow-hidden">
          {/* Graph Panel (60%) - self-contained */}
          <div className="flex-[6] min-w-0 h-full flex flex-col relative overflow-hidden bg-[#0a0a0a]">
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
                  onNodeSelect={setSelectedNodeId}
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

          {/* Note Panel (40%) - self-contained */}
          <div className="flex-[4] min-w-[280px] max-w-[480px] shrink-0 h-full flex flex-col overflow-hidden border-l border-neutral-800 bg-[#0f0f0f]">
            <NoteSidebar
              projectId={selectedProjectId}
              conceptId={selectedNodeId}
              aliases={
                projectGraph?.nodes.find((n) => n.id === selectedNodeId)
                  ?.aliases ?? []
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
