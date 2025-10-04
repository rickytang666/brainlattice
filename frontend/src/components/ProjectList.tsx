"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  IconBrain,
  IconCalendar,
  IconBook,
  IconGraph,
  IconTrash,
} from "@tabler/icons-react";
import { listProjects, deleteProject } from "@/lib/api";

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

  const handleViewGraph = (projectId: string) => {
    // Fetch project data and navigate to graph
    fetch(`http://localhost:8000/api/project/${projectId}`)
      .then((res) => res.json())
      .then((data) => {
        // Handle both old and new formats
        const graphData =
          data.project_data.graph_data || data.project_data.graph;
        sessionStorage.setItem("graphData", JSON.stringify(graphData));
        router.push("/graph");
      })
      .catch((err) => console.error("Failed to load project:", err));
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
      <Card className="p-12 text-center">
        <IconBrain className="h-16 w-16 mx-auto mb-4 text-gray-400" />
        <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          No projects yet
        </h3>
        <p className="text-gray-600 dark:text-gray-300">
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
          className="p-6 hover:shadow-lg transition-shadow cursor-pointer"
          onClick={() => handleViewGraph(project.id)}
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                {project.title}
              </h3>
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-300 mb-1">
                <IconBook className="h-4 w-4 mr-1" />
                {project.subject}
              </div>
              <div className="flex items-center text-sm text-gray-600 dark:text-gray-300 mb-1">
                <IconBrain className="h-4 w-4 mr-1" />
                {project.total_concepts} concepts
              </div>
              <div className="flex items-center text-sm text-gray-500 dark:text-gray-400">
                <IconCalendar className="h-4 w-4 mr-1" />
                {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={(e) => {
                e.stopPropagation();
                handleViewGraph(project.id);
              }}
              className="flex-1 bg-blue-600 hover:bg-blue-700"
            >
              <IconGraph className="h-4 w-4 mr-2" />
              View Graph
            </Button>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                handleDelete(project.id, project.title);
              }}
              variant="destructive"
              size="icon"
              className="shrink-0"
            >
              <IconTrash className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
