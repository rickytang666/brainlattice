import { useRef, useCallback, useMemo, useState, useEffect } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphData, ForceGraphNode, ForceGraphLink } from '../../types/graph';

interface KnowledgeGraphProps {
  data: GraphData;
}

export default function KnowledgeGraph({ data }: KnowledgeGraphProps) {
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [hoverNode, setHoverNode] = useState<string | null>(null);

  const graphData = useMemo(() => {
    const nodes: ForceGraphNode[] = data.nodes.map(n => ({ ...n }));
    const links: ForceGraphLink[] = [];

    data.nodes.forEach(node => {
      node.outbound_links.forEach(targetId => {
        if (data.nodes.find(n => n.id === targetId)) {
          links.push({
            source: node.id,
            target: targetId
          });
        }
      });
    });

    return { nodes, links };
  }, [data]);

  const handleNodeClick = useCallback((node: any) => {
    // Focus camera on node
    fgRef.current?.centerAt(node.x, node.y, 1000);
    fgRef.current?.zoom(2, 1000);
  }, []);

  const updateHighlight = () => {
    setHighlightNodes(highlightNodes);
    setHighlightLinks(highlightLinks);
  };

  const handleNodeHover = (node: any | null) => {
    highlightNodes.clear();
    highlightLinks.clear();

    if (node) {
      highlightNodes.add(node.id);
      node.neighbors = node.neighbors || [];
      node.links = node.links || [];
      
      // Calculate neighbors on the fly if needed, but react-force-graph usually adds them. 
      // Let's manually traverse based on our links for safety since we just have IDs in the props
      // Actually, react-force-graph parses the links into objects.
      
      // We need to find links connected to this node
      graphData.links.forEach((link: any) => {
        if (link.source.id === node.id || link.target.id === node.id) {
            highlightLinks.add(link);
            highlightNodes.add(link.source.id);
            highlightNodes.add(link.target.id);
        }
      });
      
      setHoverNode(node ? node.id : null);
    } else {
      setHoverNode(null);
    }
    updateHighlight();
  };

  const NODE_R = 4; // Slightly smaller radius

  // Physics tweaks
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force('charge')?.strength(-100); // Stronger repulsion for spacing
      fgRef.current.d3Force('link')?.distance(60);     // Longer links
    }
  }, []);

  return (
    <div className="w-full h-full bg-[#0a0a0a]">
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={() => ''}
        nodeColor={(node: any) => {
             const isHovered = node.id === hoverNode;
             const isNeighbor = highlightNodes.has(node.id);
             
             if (isHovered) return '#60a5fa'; // Blue
             if (isNeighbor && hoverNode) return '#9ca3af'; // Normal Grey (Keep visible)
             if (hoverNode) return '#262626'; // Dimmed
             return '#9ca3af'; // Default
        }}
        linkColor={(link: any) => {
            if (hoverNode && !highlightLinks.has(link)) return '#171717'; // Dimmed
            if (hoverNode && highlightLinks.has(link)) return 'rgba(96, 165, 250, 0.5)'; // Semi-Blue
            return '#3f3f46'; // Default
        }}
        backgroundColor="#0a0a0a"
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.id;
          const fontSize = 10 / globalScale; // Smaller font
          
          // 1. Draw Node
          ctx.beginPath();
          ctx.arc(node.x, node.y, NODE_R, 0, 2 * Math.PI, false);
          
          const isHovered = node.id === hoverNode;
          const isNeighbor = highlightNodes.has(node.id);
          
          if (isHovered) ctx.fillStyle = '#60a5fa';
          else if (isNeighbor && hoverNode) ctx.fillStyle = '#9ca3af';
          else if (hoverNode) ctx.fillStyle = '#262626';
          else ctx.fillStyle = '#9ca3af';
          
          ctx.fill();

          // 2. Draw Label
          // Show if hovered, OR if it's a neighbor of hovered, OR zoomed in
          const showLabel = (node.id === hoverNode) || (hoverNode && isNeighbor) || (globalScale >= 2.0 && !hoverNode); 

          if (showLabel) {
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Text Color
            ctx.fillStyle = (node.id === hoverNode || isNeighbor) ? '#ffffff' : 'rgba(255, 255, 255, 0.6)';
            
            // Draw on top
            ctx.fillText(label, node.x, node.y + NODE_R + (fontSize * 0.8));
          }
        }}
        onNodeHover={handleNodeHover}
        onNodeClick={handleNodeClick}
        d3AlphaDecay={0.05} // Higher decay = settles faster (less jitter)
        d3VelocityDecay={0.4} // More friction
        cooldownTicks={100} // Stop simulation after 100 ticks to freeze layout
      />
    </div>
  );
}
