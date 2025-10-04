"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import { Button } from "@/components/ui/button";

export default function GraphPage() {
  const router = useRouter();
  const [graphData, setGraphData] = useState<Record<string, unknown> | null>(
    null
  );
  const [projectId, setProjectId] = useState<string | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Get graph data and project ID from sessionStorage
    const storedData = sessionStorage.getItem("graphData");
    const storedProjectId = sessionStorage.getItem("currentProjectId");

    if (storedProjectId) {
      setProjectId(storedProjectId);
    }

    if (storedData && storedData !== "undefined" && storedData !== "null") {
      try {
        const parsed = JSON.parse(storedData);
        setGraphData(parsed);
      } catch (err) {
        console.error("Failed to parse graph data:", err);
        setError("Invalid graph data");
      }
    } else {
      setError("No graph data found");
    }
  }, [router]);

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {error}
          </h2>
          <p className="text-gray-600 dark:text-gray-300 mb-6">
            Please select a project from the home page to view its graph.
          </p>
          <Button onClick={() => router.push("/")}>← Back to Projects</Button>
        </div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <p className="text-gray-600 dark:text-gray-300">
            Loading graph data...
          </p>
        </div>
      </div>
    );
  }

  const handleBack = () => {
    if (projectId) {
      router.push(`/project/${projectId}`);
    } else {
      router.push("/");
    }
  };

  return (
    <div className="h-screen w-screen bg-gray-50 dark:bg-gray-900 p-4 flex flex-col">
      {/* Back Button */}
      <div className="mb-4">
        <Button
          onClick={handleBack}
          variant="outline"
          className="flex items-center gap-2"
        >
          ← Back to {projectId ? "Project" : "Projects"}
        </Button>
      </div>

      {/* Graph */}
      <div className="flex-1">
        <KnowledgeGraph
          graphData={
            graphData as {
              nodes: Array<{ name: string; ins: string[]; outs: string[] }>;
              graph_metadata: {
                title: string;
                subject: string;
                total_concepts: number;
                depth_levels: number;
              };
            }
          }
        />
      </div>
    </div>
  );
}
