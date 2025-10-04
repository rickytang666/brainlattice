"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  IconArrowLeft,
  IconGraph,
  IconBook,
  IconBrain,
  IconCalendar,
  IconLayersLinked,
} from "@tabler/icons-react";
import { getProject } from "@/lib/api";

interface ProjectData {
  title: string;
  subject: string;
  total_concepts: number;
  depth_levels: number;
  created_at: string;
  graph_data?: Record<string, unknown>;
  digest_data?: Record<string, unknown>;
}

export default function ProjectPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadProject = async () => {
    try {
      setLoading(true);
      const response = await getProject(projectId);

      // Handle both old and new formats
      const projectData = response.project_data as Record<string, unknown>;
      const graphData = (projectData.graph_data || projectData.graph) as Record<
        string,
        unknown
      >;
      const digestData = (projectData.digest_data ||
        projectData.reference) as Record<string, unknown>;
      const metadata = graphData?.graph_metadata as Record<string, unknown>;

      setProject({
        title:
          (projectData.title as string) ||
          (metadata?.title as string) ||
          "Untitled Project",
        subject:
          (projectData.subject as string) ||
          (metadata?.subject as string) ||
          "Unknown",
        total_concepts:
          (projectData.total_concepts as number) ||
          (metadata?.total_concepts as number) ||
          0,
        depth_levels:
          (projectData.depth_levels as number) ||
          (metadata?.depth_levels as number) ||
          0,
        created_at: projectData.created_at as string,
        graph_data: graphData,
        digest_data: digestData,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProject();
  }, [projectId]);

  const handleViewGraph = () => {
    if (project?.graph_data) {
      sessionStorage.setItem("graphData", JSON.stringify(project.graph_data));
      sessionStorage.setItem("currentProjectId", projectId);
      router.push("/graph");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-gray-600 dark:text-gray-300">
          Loading project...
        </div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <Card className="p-6 bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800">
          <p className="text-red-600 dark:text-red-400">
            {error || "Project not found"}
          </p>
          <Button onClick={() => router.push("/")} className="mt-4">
            ← Back to Projects
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Back Button */}
        <Button
          onClick={() => router.push("/")}
          variant="outline"
          className="mb-6"
        >
          <IconArrowLeft className="h-4 w-4 mr-2" />
          Back to Projects
        </Button>

        {/* Project Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            {project.title}
          </h1>
          <div className="flex flex-wrap gap-4 text-gray-600 dark:text-gray-300">
            <div className="flex items-center">
              <IconBook className="h-5 w-5 mr-2" />
              <span className="text-lg">{project.subject}</span>
            </div>
            <div className="flex items-center">
              <IconCalendar className="h-5 w-5 mr-2" />
              <span className="text-lg">
                {new Date(project.created_at).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Total Concepts
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {project.total_concepts}
                </p>
              </div>
              <IconBrain className="h-12 w-12 text-blue-600 dark:text-blue-400" />
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                  Depth Levels
                </p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {project.depth_levels}
                </p>
              </div>
              <IconLayersLinked className="h-12 w-12 text-purple-600 dark:text-purple-400" />
            </div>
          </Card>
        </div>

        {/* View Graph Button */}
        <Card className="p-8 text-center">
          <IconGraph className="h-16 w-16 mx-auto mb-4 text-blue-600 dark:text-blue-400" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Knowledge Graph
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Explore the interactive visualization of concepts and their
            relationships
          </p>
          <Button
            onClick={handleViewGraph}
            size="lg"
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
          >
            <IconGraph className="h-6 w-6 mr-2" />
            View Interactive Graph
          </Button>
        </Card>

        {/* Future sections can go here */}
        {/* e.g., Study Guide, Audio Summary, etc. */}
      </div>
    </div>
  );
}
