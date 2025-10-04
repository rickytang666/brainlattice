"use client";

import { useMemo, useRef, useEffect } from "react";
import dynamic from "next/dynamic";
import { Card } from "@/components/ui/card";

// Dynamically import ForceGraph2D to avoid SSR issues
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[600px]">
      Loading graph...
    </div>
  ),
});

interface KnowledgeGraphProps {
  graphData: {
    nodes: Array<{
      name: string;
      ins: string[];
      outs: string[];
    }>;
    graph_metadata: {
      title: string;
      subject: string;
      total_concepts: number;
      depth_levels: number;
    };
  };
}

export default function KnowledgeGraph({ graphData }: KnowledgeGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(undefined);

  // Customize link distance after mount
  useEffect(() => {
    if (fgRef.current) {
      // Make links longer by increasing link distance
      fgRef.current.d3Force("link").distance(150);
      // Increase charge repulsion to push nodes further apart
      fgRef.current.d3Force("charge").strength(-400);
    }
  }, []);

  // Convert to react-force-graph format
  const graphForceData = useMemo(() => {
    // Create a map of node names to their data
    const nodeDataMap = new Map(graphData.nodes.map((n) => [n.name, n]));

    // Collect all unique node names
    const allNodeNames = new Set<string>();

    graphData.nodes.forEach((node) => {
      allNodeNames.add(node.name);
      node.ins.forEach((name) => allNodeNames.add(name));
      node.outs.forEach((name) => allNodeNames.add(name));
    });

    // Create nodes array with size based on outs length
    const nodes = Array.from(allNodeNames).map((name) => {
      const nodeData = nodeDataMap.get(name);
      const outsCount = nodeData?.outs.length || 0;
      // Size based on number of outs: min 2, max 12
      const nodeSize = 1 + outsCount * 0.5;

      return {
        id: name,
        name: name,
        val: nodeSize, // This sets the node size in react-force-graph
      };
    });

    // Create links array (edges)
    const links: Array<{ source: string; target: string }> = [];
    const linkSet = new Set<string>();

    graphData.nodes.forEach((node) => {
      // Connect outgoing nodes (this node → out node)
      node.outs.forEach((outNode) => {
        const linkId = `${node.name}-${outNode}`;
        if (!linkSet.has(linkId) && allNodeNames.has(outNode)) {
          linkSet.add(linkId);
          links.push({
            source: node.name,
            target: outNode,
          });
        }
      });

      // Connect incoming nodes (in node → this node)
      node.ins.forEach((inNode) => {
        const linkId = `${inNode}-${node.name}`;
        if (!linkSet.has(linkId) && allNodeNames.has(inNode)) {
          linkSet.add(linkId);
          links.push({
            source: inNode,
            target: node.name,
          });
        }
      });
    });

    return { nodes, links };
  }, [graphData]);

  return (
    <div className="w-full">
      <Card className="p-4 mb-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              {graphData.graph_metadata.title}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {graphData.graph_metadata.subject} •{" "}
              {graphData.graph_metadata.total_concepts} concepts
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Depth: {graphData.graph_metadata.depth_levels} levels
            </p>
          </div>
        </div>
      </Card>

      <div
        className="border rounded-lg overflow-hidden bg-white dark:bg-gray-900"
        style={{ height: "calc(100vh - 200px)" }}
      >
        <ForceGraph2D
          ref={fgRef}
          graphData={graphForceData}
          nodeLabel="name"
          nodeAutoColorBy="id"
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkColor={() => "#94a3b8"}
          linkWidth={1}
          nodeRelSize={3}
          enableNodeDrag={true}
          enableZoomInteraction={true}
          enablePanInteraction={true}
          d3AlphaDecay={0.01}
          d3VelocityDecay={0.2}
          cooldownTime={5000}
          linkDirectionalParticles={0}
        />
      </div>

      <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
        <p className="text-sm text-gray-600 dark:text-gray-300">
          💡 <strong>Tip:</strong> Drag nodes to rearrange • Scroll to zoom •
          Click and drag background to pan
        </p>
      </div>
    </div>
  );
}
