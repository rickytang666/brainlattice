"use client";

import { useEffect, useState } from "react";
import KnowledgeGraph from "@/components/KnowledgeGraph";

export default function GraphPage() {
  const [graphData, setGraphData] = useState<Record<string, unknown> | null>(
    null
  );

  useEffect(() => {
    // Get graph data from sessionStorage
    const storedData = sessionStorage.getItem("graphData");
    if (storedData) {
      setGraphData(JSON.parse(storedData));
    }
  }, []);

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

  return (
    <div className="h-screen w-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="h-full">
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
