"use client";

import { useMemo, useRef, useEffect, useState, useCallback } from "react";
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

interface GraphNode {
  id: string;
  name: string;
  val: number;
  [key: string]: unknown;
}

export default function KnowledgeGraph({ graphData }: KnowledgeGraphProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(undefined);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [prerequisiteNodes, setPrerequisiteNodes] = useState(new Set<string>());
  const [dependentNodes, setDependentNodes] = useState(new Set<string>());

  // Customize link distance after mount
  useEffect(() => {
    if (fgRef.current) {
      // Set shorter link distance for tighter graph
      fgRef.current.d3Force("link").distance(10);
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

  // Handle node hover - highlight connected nodes and links
  const handleNodeHover = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (node: any) => {
      setHoveredNode(node);

      // Pause/resume graph physics when hovering
      if (fgRef.current) {
        if (node) {
          // Pause the simulation when hovering
          fgRef.current.pauseAnimation();
        } else {
          // Resume the simulation when not hovering
          fgRef.current.resumeAnimation();
        }
      }

      if (!node) {
        setHighlightNodes(new Set());
        setHighlightLinks(new Set());
        setPrerequisiteNodes(new Set());
        setDependentNodes(new Set());
        return;
      }

      const connectedNodes = new Set<string>();
      const connectedLinks = new Set<string>();
      const prerequisites = new Set<string>();
      const dependents = new Set<string>();

      // Add the hovered node itself
      connectedNodes.add(node.id);

      // Find all links connected to this node
      graphForceData.links.forEach((link) => {
        const sourceId =
          typeof link.source === "object" && link.source !== null
            ? (link.source as { id: string }).id
            : String(link.source);
        const targetId =
          typeof link.target === "object" && link.target !== null
            ? (link.target as { id: string }).id
            : String(link.target);

        if (sourceId === node.id || targetId === node.id) {
          // Add the link
          connectedLinks.add(`${sourceId}-${targetId}`);

          // Differentiate between prerequisites (ins) and dependents (outs)
          if (sourceId === node.id) {
            // This node points to targetId, so targetId is a dependent (out)
            connectedNodes.add(targetId);
            dependents.add(targetId);
          } else {
            // sourceId points to this node, so sourceId is a prerequisite (in)
            connectedNodes.add(sourceId);
            prerequisites.add(sourceId);
          }
        }
      });

      setHighlightNodes(connectedNodes);
      setHighlightLinks(connectedLinks);
      setPrerequisiteNodes(prerequisites);
      setDependentNodes(dependents);
    },
    [graphForceData.links]
  );

  // Generate consistent color from string (hash-based)
  const getNodeDefaultColor = useCallback((nodeId: string): string => {
    let hash = 0;
    for (let i = 0; i < nodeId.length; i++) {
      hash = nodeId.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash % 360);
    return `hsl(${hue}, 70%, 60%)`;
  }, []);

  // Custom node color based on hover state
  const nodeColor = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (node: any): string => {
      if (!hoveredNode) {
        // Default: colorful nodes based on ID
        return getNodeDefaultColor(node.id);
      }

      if (node.id === hoveredNode.id) {
        // Hovered node - bright highlight
        return "#ef4444"; // red-500
      }

      if (prerequisiteNodes.has(node.id)) {
        // Prerequisites (ins) - blue
        return "#3b82f6"; // blue-500
      }

      if (dependentNodes.has(node.id)) {
        // Dependents (outs) - green
        return "#10b981"; // emerald-500
      }

      // Dimmed nodes
      return "#d1d5db"; // gray-300
    },
    [hoveredNode, prerequisiteNodes, dependentNodes, getNodeDefaultColor]
  );

  // Custom link color based on hover state
  const linkColor = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (link: any) => {
      if (!hoveredNode) {
        return "#94a3b8"; // slate-400 - default
      }

      const sourceId =
        typeof link.source === "object" && link.source !== null
          ? (link.source as { id: string }).id
          : String(link.source);
      const targetId =
        typeof link.target === "object" && link.target !== null
          ? (link.target as { id: string }).id
          : String(link.target);
      const linkId = `${sourceId}-${targetId}`;

      if (highlightLinks.has(linkId)) {
        return "#ef4444"; // red-500 - highlighted
      }

      return "#e5e7eb"; // gray-200 - dimmed
    },
    [hoveredNode, highlightLinks]
  );

  // Custom link width based on hover state
  const linkWidth = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (link: any) => {
      if (!hoveredNode) {
        return 1;
      }

      const sourceId =
        typeof link.source === "object" && link.source !== null
          ? (link.source as { id: string }).id
          : String(link.source);
      const targetId =
        typeof link.target === "object" && link.target !== null
          ? (link.target as { id: string }).id
          : String(link.target);
      const linkId = `${sourceId}-${targetId}`;

      return highlightLinks.has(linkId) ? 3 : 0.5;
    },
    [hoveredNode, highlightLinks]
  );

  // Custom node opacity based on hover state
  const nodeCanvasObject = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (node: any, ctx: CanvasRenderingContext2D) => {
      if (!hoveredNode) {
        // Default rendering
        return;
      }

      // Set opacity for dimmed nodes
      if (node.id !== hoveredNode.id && !highlightNodes.has(node.id)) {
        ctx.globalAlpha = 0.2;
      } else {
        ctx.globalAlpha = 1;
      }
    },
    [hoveredNode, highlightNodes]
  );

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
          nodeColor={nodeColor}
          onNodeHover={handleNodeHover}
          nodeCanvasObjectMode="before"
          nodeCanvasObject={nodeCanvasObject}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkColor={linkColor}
          linkWidth={linkWidth}
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
          💡 <strong>Tip:</strong> Hover over nodes to see connections • Drag
          nodes to rearrange • Scroll to zoom • Click and drag background to pan
        </p>
        {hoveredNode && (
          <div className="text-sm text-gray-900 dark:text-white mt-2">
            <p className="mb-1">
              <strong>Hovering:</strong> {hoveredNode.name}
            </p>
            <div className="flex gap-4 flex-wrap">
              <span className="flex items-center gap-1">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: "#3b82f6" }}
                ></span>
                <span className="text-blue-500">
                  {prerequisiteNodes.size} prerequisites (ins)
                </span>
              </span>
              <span className="flex items-center gap-1">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: "#10b981" }}
                ></span>
                <span className="text-emerald-500">
                  {dependentNodes.size} dependents (outs)
                </span>
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
