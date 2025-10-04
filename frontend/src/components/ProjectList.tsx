"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  IconBrain,
  IconCalendar,
  IconBook,
  IconArrowRight,
} from "@tabler/icons-react";
import { listProjects } from "@/lib/api";

interface Project {
  id: string;
  graph?: {
    graph_metadata?: {
      title?: string;
      subject?: string;
      total_concepts?: number;
      depth_levels?: number;
    };
  };
  created_at?: {
    seconds: number;
  };
}

interface ProjectListProps {
  onProjectSelect: (projectId: string) => void;
}

export default function ProjectList({ onProjectSelect }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const projectList = await listProjects();
      setProjects(projectList);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
        <Button onClick={loadProjects} variant="outline">
          Retry
        </Button>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="text-center py-8">
        <IconBrain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          No projects found
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Upload your first PDF to get started!
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        Your Knowledge Graphs
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects.map((project) => (
          <Card
            key={project.id}
            className="p-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => onProjectSelect(project.id)}
          >
            <div className="flex items-start justify-between mb-3">
              <IconBrain className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              <IconArrowRight className="h-4 w-4 text-gray-400" />
            </div>

            <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
              {project.graph?.graph_metadata?.title || "Untitled Project"}
            </h3>

            <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
              <div className="flex items-center">
                <IconBook className="h-4 w-4 mr-2" />
                <span>
                  {project.graph?.graph_metadata?.subject || "Unknown Subject"}
                </span>
              </div>

              <div className="flex items-center">
                <IconCalendar className="h-4 w-4 mr-2" />
                <span>
                  {project.created_at
                    ? new Date(
                        project.created_at.seconds * 1000
                      ).toLocaleDateString()
                    : "Unknown Date"}
                </span>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>
                  {project.graph?.graph_metadata?.total_concepts || 0} concepts
                </span>
                <span>
                  {project.graph?.graph_metadata?.depth_levels || 0} levels
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
