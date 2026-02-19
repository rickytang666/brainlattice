import { useRef, useCallback, useMemo, useState, useEffect } from 'react';
import ForceGraph2D, { type ForceGraphMethods } from 'react-force-graph-2d';
import type { GraphData, ForceGraphNode, ForceGraphLink } from '../../types/graph';

interface KnowledgeGraphProps {
  data: GraphData;
}

// Helper: Linear Interpolation for Hex Colors
const lerpColor = (a: string, b: string, t: number) => {
  const ah = parseInt(a.replace(/#/g, ''), 16),
        ar = ah >> 16, ag = ah >> 8 & 0xff, ab = ah & 0xff,
        bh = parseInt(b.replace(/#/g, ''), 16),
        br = bh >> 16, bg = bh >> 8 & 0xff, bb = bh & 0xff,
        rr = ar + t * (br - ar),
        rg = ag + t * (bg - ag),
        rb = ab + t * (bb - ab);
  return '#' + ((1 << 24) + (rr << 16) + (rg << 8) + rb | 0).toString(16).slice(1);
};

export default function KnowledgeGraph({ data }: KnowledgeGraphProps) {
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<string>());
  const [hoverNode, setHoverNode] = useState<string | null>(null);
  
  // Transition State (0 = Normal, 1 = Full Hover Effect)
  const [transitionLevel, setTransitionLevel] = useState(0); 
  const animationRef = useRef<number>(0);

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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeClick = useCallback((node: any) => {
    // Focus camera on node
    fgRef.current?.centerAt(node.x, node.y, 1000);
    fgRef.current?.zoom(2, 1000);
  }, []);

  const updateHighlight = () => {
    setHighlightNodes(highlightNodes);
    setHighlightLinks(highlightLinks);
  };

  // Animation Loop for Smooth Transitions
  useEffect(() => {
    const targetLevel = hoverNode ? 1 : 0;
    
    const animate = () => {
      setTransitionLevel(prev => {
        const delta = targetLevel - prev;
        const speed = 0.1; // Adjust for 0.5s feel (depends on frame rate, approx 60fps * 0.1 step)
        
        if (Math.abs(delta) < 0.01) {
            return targetLevel;
        }
        return prev + delta * speed;
      });
      
      if (Math.abs(targetLevel - transitionLevel) > 0.01) {
          animationRef.current = requestAnimationFrame(animate);
      }
    };
    
    animationRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationRef.current!);
  }, [hoverNode, transitionLevel]); // Dependency on transitionLevel ensures loop continues

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleNodeHover = (node: any | null) => {
    // Instant update, animation handles the fade
    highlightNodes.clear();
    highlightLinks.clear();

    if (node) {
      highlightNodes.add(node.id);
      node.neighbors = node.neighbors || [];
      node.links = node.links || [];
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      graphData.links.forEach((link: any) => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;
        
        if (sourceId === node.id || targetId === node.id) {
            highlightLinks.add(link);
            highlightNodes.add(sourceId);
            highlightNodes.add(targetId);
        }
      });
      
      setHoverNode(node.id);
    } else {
      setHoverNode(null);
    }
    updateHighlight();
  };

  const NODE_R = 4; // Slightly smaller radius
  
  // Colors
  const COL_DEFAULT = '#9ca3af'; // zinc-400
  const COL_HIGHLIGHT = '#60a5fa'; // blue-400
  const COL_DIM = '#262626'; // zinc-800
  const COL_LINK_DEFAULT = '#3f3f46';
  const COL_LINK_DIM = '#171717';

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
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeColor={(node: any) => {
             // Target Logic
             let targetColor = COL_DEFAULT;
             if (hoverNode) {
                 if (node.id === hoverNode) targetColor = COL_HIGHLIGHT;
                 else if (highlightNodes.has(node.id)) targetColor = COL_DEFAULT; // Neighbors stay grey
                 else targetColor = COL_DIM; // Others dim
             }
             
             // Interpolate: Base (Default) -> Target (Focus State)
             return lerpColor(COL_DEFAULT, targetColor, transitionLevel);
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkColor={(link: any) => {
            let targetColor = COL_LINK_DEFAULT;
            if (hoverNode) {
                 if (highlightLinks.has(link)) targetColor = COL_HIGHLIGHT;
                 else targetColor = COL_LINK_DIM;
            }
            return lerpColor(COL_LINK_DEFAULT, targetColor, transitionLevel);
        }}
        backgroundColor="#0a0a0a"
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const label = node.id;
          const fontSize = 10 / globalScale; // Smaller font
          
          // 1. Draw Node
          ctx.beginPath();
          ctx.arc(node.x, node.y, NODE_R, 0, 2 * Math.PI, false);
          
          // Use the interpolated color logic
          let targetColor = COL_DEFAULT;
          if (hoverNode) {
             if (node.id === hoverNode) targetColor = COL_HIGHLIGHT;
             else if (highlightNodes.has(node.id)) targetColor = COL_DEFAULT;
             else targetColor = COL_DIM;
          }
          ctx.fillStyle = lerpColor(COL_DEFAULT, targetColor, transitionLevel);
          
          ctx.fill();

          // 2. Draw Label
          const isNeighbor = highlightNodes.has(node.id);
          const showLabel = (node.id === hoverNode) || (hoverNode && isNeighbor && globalScale >= 1.5) || (globalScale >= 2.0 && !hoverNode); 

          if (showLabel) {
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            
            // Fade text opacity
            const opacity = node.id === hoverNode || isNeighbor ? transitionLevel : 0.6;
            ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`;
            
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
