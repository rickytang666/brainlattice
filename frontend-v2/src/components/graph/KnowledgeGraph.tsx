import { useRef, useCallback, useMemo, useState } from 'react';
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
      
      setHoverNode(node.id);
    } else {
      setHoverNode(null);
    }
    updateHighlight();
  };

  const NODE_R = 5;

  return (
    <div className="w-full h-full bg-[#0a0a0a]">
      <ForceGraph2D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={() => ''} // Disable default label
        nodeColor={(node: any) => {
             if (hoverNode && !highlightNodes.has(node.id)) return '#262626'; // Dimmed (zinc-800)
             if (hoverNode && highlightNodes.has(node.id)) return '#60a5fa'; // Highlighted (blue-400)
             return '#9ca3af'; // Default (zinc-400)
        }}
        linkColor={(link: any) => {
            if (hoverNode && !highlightLinks.has(link)) return '#171717'; // Dimmed
            if (hoverNode && highlightLinks.has(link)) return '#60a5fa'; // Highlighted
            return '#3f3f46'; // Default
        }}
        backgroundColor="#0a0a0a"
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        nodeCanvasObject={(node: any, ctx, globalScale) => {
          const label = node.id;
          const fontSize = 12 / globalScale;
          
          // 1. Draw Node
          ctx.beginPath();
          ctx.arc(node.x, node.y, NODE_R, 0, 2 * Math.PI, false);
          ctx.fillStyle = (hoverNode && !highlightNodes.has(node.id)) 
            ? '#262626' 
            : (hoverNode && highlightNodes.has(node.id) ? '#60a5fa' : '#9ca3af');
          ctx.fill();

          // 2. Draw Label logic
          // Make label visible if:
          // a) We are hovering this node or its neighbor
          // b) We are zoomed in close enough (Obsidian behavior)
          const isHighlighted = highlightNodes.has(node.id);
          const showLabel = (hoverNode && isHighlighted) || globalScale >= 1.5;

          if (showLabel) {
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Highlighted nodes get brighter text
            ctx.fillStyle = isHighlighted ? '#ffffff' : 'rgba(255, 255, 255, 0.6)';
            
            ctx.fillText(label, node.x, node.y + NODE_R + (fontSize * 0.8));
          }
        }}
        onNodeHover={handleNodeHover}
        onNodeClick={handleNodeClick}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
      />
    </div>
  );
}
