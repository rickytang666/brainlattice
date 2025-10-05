"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import KnowledgeGraph from "@/components/KnowledgeGraph";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import Logo from "@/components/Logo";
import { IconArrowLeft } from "@tabler/icons-react";

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
      <div className="min-h-screen bg-grid-pattern">
        {/* Header */}
        <header className="flex justify-between items-center p-6 border-b border-cyan-500/30 backdrop-blur-sm bg-background/80">
          <Logo size="md" showText={true} />
          <ThemeToggle />
        </header>

        <div className="flex items-center justify-center h-[calc(100vh-80px)]">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-foreground mb-4 font-mono">
              {error}
            </h2>
            <p className="text-muted-foreground mb-6 text-lg">
              Please select a project from the home page to view its graph.
            </p>
            <Button
              onClick={() => router.push("/projects")}
              className="bg-cyan-500 hover:bg-cyan-600 text-black font-semibold font-mono tracking-wide"
            >
              <IconArrowLeft className="h-4 w-4 mr-2" />
              BACK TO PROJECTS
            </Button>
          </div>
        </div>
      </div>
    );
  }

  if (!graphData) {
    return (
      <div className="min-h-screen bg-grid-pattern">
        {/* Header */}
        <header className="flex justify-between items-center p-6 border-b border-cyan-500/30 backdrop-blur-sm bg-background/80">
          <Logo size="md" showText={true} />
          <ThemeToggle />
        </header>

        <div className="flex items-center justify-center h-[calc(100vh-80px)]">
          <div className="text-center">
            <p className="text-muted-foreground text-lg font-mono">
              LOADING GRAPH DATA...
            </p>
          </div>
        </div>
      </div>
    );
  }

  const handleBack = () => {
    if (projectId) {
      router.push(`/project/${projectId}`);
    } else {
      router.push("/projects");
    }
  };

  return (
    <div className="min-h-screen bg-grid-pattern">
      {/* Header */}
      <header className="flex justify-between items-center p-6 border-b border-cyan-500/30 backdrop-blur-sm bg-background/80">
        <Logo size="md" showText={true} />
        <ThemeToggle />
      </header>

      <div className="p-6 flex flex-col h-[calc(100vh-80px)]">
        {/* Back Button */}
        <div className="mb-6">
          <Button
            onClick={handleBack}
            variant="outline"
            className="border-cyan-500/50 text-cyan-400 hover:bg-cyan-500/10 hover:text-cyan-300 font-mono"
          >
            <IconArrowLeft className="h-4 w-4 mr-2" />
            BACK TO {projectId ? "PROJECT" : "PROJECTS"}
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
    </div>
  );
}
