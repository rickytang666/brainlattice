"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  IconBrain,
  IconCalendar,
  IconBook,
  IconGraph,
  IconTrash,
  IconEdit,
  IconCheck,
  IconX,
} from "@tabler/icons-react";
import { listProjects, deleteProject, updateProjectTitle } from "@/lib/api";

interface Project {
  id: string;
  title: string;
  subject: string;
  total_concepts: number;
  created_at: string;
}

export default function ProjectList() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await listProjects();
      // Map the response to our Project interface
      const mappedProjects: Project[] = (data || []).map(
        (p: Record<string, unknown>) => {
          // Handle both new and old Firebase formats
          let title = "Untitled";
          let subject = "Unknown";
          let totalConcepts = 0;

          if (p.title) {
            // New format with metadata at root
            title = p.title as string;
            subject = (p.subject as string) || "Unknown";
            totalConcepts = (p.total_concepts as number) || 0;
          } else if (p.graph && typeof p.graph === "object") {
            // Old format with nested graph_data
            const graph = p.graph as Record<string, unknown>;
            const metadata = graph.graph_metadata as Record<string, unknown>;
            if (metadata) {
              title = (metadata.title as string) || "Untitled";
              subject = (metadata.subject as string) || "Unknown";
              totalConcepts = (metadata.total_concepts as number) || 0;
            }
          }

          return {
            id: (p.id as string) || "",
            title,
            subject,
            total_concepts: totalConcepts,
            created_at: (p.created_at as string) || new Date().toISOString(),
          };
        }
      );
      setProjects(mappedProjects);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  const handleViewProject = (projectId: string) => {
    router.push(`/project/${projectId}`);
  };

  const handleStartEdit = (projectId: string, currentTitle: string) => {
    setEditingId(projectId);
    setEditTitle(currentTitle);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleSaveEdit = async (projectId: string) => {
    if (!editTitle.trim()) {
      alert("Title cannot be empty");
      return;
    }

    try {
      await updateProjectTitle(projectId, editTitle.trim());
      // Update local state
      setProjects(
        projects.map((p) =>
          p.id === projectId ? { ...p, title: editTitle.trim() } : p
        )
      );
      setEditingId(null);
      setEditTitle("");
    } catch (err) {
      console.error("Failed to update title:", err);
      alert("Failed to update title. Please try again.");
    }
  };

  const handleDelete = async (projectId: string, projectTitle: string) => {
    if (!confirm(`Are you sure you want to delete "${projectTitle}"?`)) {
      return;
    }

    try {
      await deleteProject(projectId);
      // Refresh the project list
      loadProjects();
    } catch (err) {
      console.error("Failed to delete project:", err);
      alert("Failed to delete project. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-gray-600 dark:text-gray-300">
          Loading projects...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="p-6 bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
        <p className="text-red-600 dark:text-red-400">{error}</p>
      </Card>
    );
  }

  if (projects.length === 0) {
    return (
      <Card className="p-16 text-center border-cyan-500/30 bg-card/50 backdrop-blur-sm">
        <IconBrain className="h-20 w-20 mx-auto mb-6 text-cyan-400/50" />
        <h3 className="text-2xl font-bold text-foreground mb-3 font-mono tracking-wide">
          NO PROJECTS YET
        </h3>
        <p className="text-muted-foreground text-lg font-light">
          Upload your first PDF to get started!
        </p>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((project) => (
        <Card
          key={project.id}
          className="p-6 hover:border-cyan-500/50 transition-all duration-300 cursor-pointer border-cyan-500/20 bg-card/50 backdrop-blur-sm hover:shadow-cyan-500/20 hover:shadow-lg group flex flex-col h-full"
          onClick={() => handleViewProject(project.id)}
        >
          <div className="flex items-start justify-between mb-4 flex-1">
            <div className="flex-1">
              {editingId === project.id ? (
                <div className="flex items-center gap-2 mb-2">
                  <Input
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="text-lg font-semibold"
                    autoFocus
                  />
                  <Button
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSaveEdit(project.id);
                    }}
                    className="bg-green-600 hover:bg-green-700 shrink-0"
                  >
                    <IconCheck className="h-4 w-4" />
                  </Button>
                  <Button
                    size="icon"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCancelEdit();
                    }}
                    className="shrink-0"
                  >
                    <IconX className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="text-lg font-bold text-foreground line-clamp-2 flex-1 group-hover:text-cyan-400 transition-colors">
                    {project.title}
                  </h3>
                  <Button
                    size="icon"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(project.id, project.title);
                    }}
                    className="shrink-0 h-8 w-8 hover:text-cyan-400 hover:bg-cyan-500/10"
                  >
                    <IconEdit className="h-4 w-4" />
                  </Button>
                </div>
              )}
              <div className="flex items-center text-sm text-muted-foreground mb-1 font-mono">
                <IconBook className="h-4 w-4 mr-2 text-cyan-400/70" />
                {project.subject}
              </div>
              <div className="flex items-center text-sm text-muted-foreground mb-1 font-mono">
                <IconBrain className="h-4 w-4 mr-2 text-cyan-400/70" />
                {project.total_concepts} concepts
              </div>
              <div className="flex items-center text-sm text-muted-foreground/70 font-mono">
                <IconCalendar className="h-4 w-4 mr-2 text-cyan-400/50" />
                {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          <div className="flex gap-2 mt-auto">
            <Button
              onClick={(e) => {
                e.stopPropagation();
                handleViewProject(project.id);
              }}
              className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-black font-semibold font-mono tracking-wide"
            >
              <IconGraph className="h-4 w-4 mr-2" />
              VIEW
            </Button>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(project.id, project.title);
              }}
              variant="destructive"
              size="icon"
              className="shrink-0 hover:bg-red-600"
            >
              <IconTrash className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
