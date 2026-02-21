import { useRef, useCallback, useMemo, useState, useEffect } from "react";
import ForceGraph2D, { type ForceGraphMethods } from "react-force-graph-2d";
import type {
  GraphData,
  ForceGraphNode,
  ForceGraphLink,
} from "../../types/graph";
import { useTheme } from "../ThemeProvider";

// explicit dimensions so graph centers in its panel, not the screen
function useContainerSize() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 800, height: 600 });

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const updateSize = () => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        setSize({ width: rect.width, height: rect.height });
      }
    };

    updateSize();
    const ro = new ResizeObserver(updateSize);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return { containerRef, ...size };
}

interface KnowledgeGraphProps {
  data: GraphData;
  onNodeSelect?: (nodeId: string | null) => void;
  focusNodeId?: string | null;
  onFocusComplete?: () => void;
}

// Helper: Linear Interpolation for Hex Colors
const lerpColor = (a: string, b: string, t: number) => {
  const ah = parseInt(a.replace(/#/g, ""), 16),
    ar = ah >> 16,
    ag = (ah >> 8) & 0xff,
    ab = ah & 0xff,
    bh = parseInt(b.replace(/#/g, ""), 16),
    br = bh >> 16,
    bg = (bh >> 8) & 0xff,
    bb = bh & 0xff,
    rr = ar + t * (br - ar),
    rg = ag + t * (bg - ag),
    rb = ab + t * (bb - ab);
  return (
    "#" + (((1 << 24) + (rr << 16) + (rg << 8) + rb) | 0).toString(16).slice(1)
  );
};

// static theme palette
const THEME_COLORS = {
  light: {
    background: "#e7e5e4",
    foreground: "#1e293b",
    primary: "#069eb9",
    mutedForeground: "#6b7280",
    border: "#d6d3d1",
  },
  dark: {
    background: "#1e1b18",
    foreground: "#e2e8f0",
    primary: "#07b7d6",
    mutedForeground: "#9ca3af",
    border: "#3a3633",
  },
};

type GraphLinkType = ForceGraphLink | { source: ForceGraphNode; target: ForceGraphNode };

export default function KnowledgeGraph({
  data,
  onNodeSelect,
  focusNodeId,
  onFocusComplete,
}: KnowledgeGraphProps) {
  const { containerRef, width, height } = useContainerSize();
  const fgRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [highlightNodes, setHighlightNodes] = useState(new Set<string>());
  const [highlightLinks, setHighlightLinks] = useState(new Set<GraphLinkType>());
  const [hoverNode, setHoverNode] = useState<string | null>(null);

  // Transition State (0 = Normal, 1 = Full Hover Effect)
  const [transitionLevel, setTransitionLevel] = useState(0);
  const animationRef = useRef<number>(0);
  const { theme } = useTheme();

  // determine current active palette (handles "system" preference fallback assuming dark for now - can optimize later)
  const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  const palette = isDark ? THEME_COLORS.dark : THEME_COLORS.light;

  const graphData = useMemo(() => {
    const nodes: ForceGraphNode[] = data.nodes.map((n) => ({ ...n }));
    const links: ForceGraphLink[] = [];
    const linkCount: Record<string, number> = {};

    data.nodes.forEach((node) => {
      linkCount[node.id] = 0;
      node.outbound_links.forEach((targetId) => {
        if (data.nodes.find((n) => n.id === targetId)) {
          links.push({ source: node.id, target: targetId });
          linkCount[node.id] = (linkCount[node.id] ?? 0) + 1;
          linkCount[targetId] = (linkCount[targetId] ?? 0) + 1;
        }
      });
    });

    const maxLinks = Math.max(1, ...Object.values(linkCount));
    nodes.forEach((n) => {
      const gNode = n as ForceGraphNode & { connectivity?: number; normConnectivity?: number };
      gNode.connectivity = linkCount[n.id] ?? 0;
      gNode.normConnectivity = (linkCount[n.id] ?? 0) / maxLinks;
    });

    return { nodes, links };
  }, [data]);

   
  const handleNodeClick = useCallback(
    (node: ForceGraphNode) => {
      onNodeSelect?.(node.id);
    },
    [onNodeSelect],
  );

  const updateHighlight = () => {
    setHighlightNodes(highlightNodes);
    setHighlightLinks(highlightLinks);
  };

  // Animation Loop for Smooth Transitions
  useEffect(() => {
    const targetLevel = hoverNode ? 1 : 0;

    const animate = () => {
      setTransitionLevel((prev) => {
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

  const handleNodeHover = (node: ForceGraphNode | null) => {
    // Instant update, animation handles the fade
    highlightNodes.clear();
    highlightLinks.clear();

    if (node) {
      highlightNodes.add(node.id);

      graphData.links.forEach((link: GraphLinkType) => {
        const sourceId =
          typeof link.source === "object" ? link.source.id : link.source;
        const targetId =
          typeof link.target === "object" ? link.target.id : link.target;

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

  const NODE_R_BASE = 3;
  const NODE_R_EXTRA = 5; // more connected = bigger (range 3 to ~7)
  const ZOOM_LABEL_BREAKPOINT = 2;

  // Colors based on current theme
  const COL_DEFAULT = palette.mutedForeground; 
  const COL_HIGHLIGHT = palette.primary; 
  const COL_DIM = palette.border; 
  const COL_LINK_DEFAULT = palette.border; 
  const COL_LINK_DIM = palette.background; 

  // Physics tweaks
  useEffect(() => {
    if (fgRef.current) {
      fgRef.current.d3Force("charge")?.strength(-100); // Stronger repulsion for spacing
      fgRef.current.d3Force("link")?.distance(60); // Longer links
    }
  }, []);

  // Focus on node when focusNodeId is set
  useEffect(() => {
    if (!focusNodeId || !fgRef.current || !graphData.nodes.length) return;
    const node = graphData.nodes.find((n) => n.id === focusNodeId);
    if (!node || node.x == null || node.y == null) return;

    const zoomLevel = 5;
    const duration = 400;
    fgRef.current.centerAt(node.x, node.y, duration);
    fgRef.current.zoom(zoomLevel, duration);
    onFocusComplete?.();
  }, [focusNodeId, graphData.nodes, onFocusComplete]);

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full bg-background"
    >
      <ForceGraph2D
        // @ts-expect-error third-party package type mismatch
        ref={fgRef}
        width={width}
        height={height}
        graphData={graphData}
        nodeLabel={() => ""}
        nodeColor={(node: ForceGraphNode) => {
          // Target Logic
          let targetColor = COL_DEFAULT;
          if (hoverNode) {
            if (node.id === hoverNode) targetColor = COL_HIGHLIGHT;
            else if (highlightNodes.has(node.id))
              targetColor = COL_DEFAULT; // Neighbors stay grey
            else targetColor = COL_DIM; // Others dim
          }

          // Interpolate: Base (Default) -> Target (Focus State)
          return lerpColor(COL_DEFAULT, targetColor, transitionLevel);
        }}
        linkColor={(link: GraphLinkType) => {
          let targetColor = COL_LINK_DEFAULT;
          if (hoverNode) {
            if (highlightLinks.has(link)) targetColor = COL_HIGHLIGHT;
            else targetColor = COL_LINK_DIM;
          }
          return lerpColor(COL_LINK_DEFAULT, targetColor, transitionLevel);
        }}
        backgroundColor={palette.background}
        linkDirectionalArrowLength={3.5}
        linkDirectionalArrowRelPos={1}
         
        nodeCanvasObject={(
          node: ForceGraphNode,
          ctx: CanvasRenderingContext2D,
          globalScale: number,
        ) => {
          const label = node.id;
          const fontSize = 10 / globalScale;

          // Radius by connectivity (sqrt for subtle spread: base 3, max ~5.5)
          const norm = (node as ForceGraphNode & { normConnectivity?: number }).normConnectivity ?? 0;
          const nodeR =
            NODE_R_BASE + NODE_R_EXTRA * Math.sqrt(Math.min(1, norm));

          // 1. Draw Node
          ctx.beginPath();
          if (node.x != null && node.y != null) {
            ctx.arc(node.x, node.y, nodeR, 0, 2 * Math.PI, false);
          }
          
          // Use the interpolated color logic
          let targetColor = COL_DEFAULT;
          if (hoverNode) {
            if (node.id === hoverNode) targetColor = COL_HIGHLIGHT;
            else if (highlightNodes.has(node.id)) targetColor = COL_DEFAULT;
            else targetColor = COL_DIM;
          }
          ctx.fillStyle = lerpColor(COL_DEFAULT, targetColor, transitionLevel);

          ctx.fill();

          // 2. Draw Label (uniform breakpoint: zoomed in = labels + neighbors on hover; zoomed out = only hovered node)
          const zoomedIn = globalScale >= ZOOM_LABEL_BREAKPOINT;
          const isNeighbor = highlightNodes.has(node.id);
          const showLabel = zoomedIn
            ? !hoverNode || node.id === hoverNode || isNeighbor
            : node.id === hoverNode;

          if (showLabel) {
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";

            // Fade text opacity
            const opacity =
              node.id === hoverNode || isNeighbor ? transitionLevel : 0.6;
            
            // Text color from palette
            const r = parseInt(palette.foreground.slice(1, 3), 16);
            const g = parseInt(palette.foreground.slice(3, 5), 16);
            const b = parseInt(palette.foreground.slice(5, 7), 16);
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${opacity})`;

            if (node.x != null && node.y != null) {
              ctx.fillText(label, node.x, node.y + nodeR + fontSize * 0.8);
            }
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
