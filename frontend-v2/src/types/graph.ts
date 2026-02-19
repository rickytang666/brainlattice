export interface Node {
  id: string;
  aliases: string[];
  outbound_links: string[];
  inbound_links: string[];
  description?: string;
  metadata?: Record<string, any>;
}

export interface GraphData {
  nodes: Node[];
}

export interface ForceGraphNode extends Node {
  x?: number;
  y?: number;
  z?: number;
}

export interface ForceGraphLink {
  source: string;
  target: string;
}
