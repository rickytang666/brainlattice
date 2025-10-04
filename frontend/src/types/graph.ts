export interface GraphMetadata {
  title: string;
  subject: string;
  total_concepts: number;
  depth_levels: number;
}

export interface GraphData {
  nodes: Array<{
    name: string;
    ins: string[];
    outs: string[];
  }>;
  graph_metadata: GraphMetadata;
}

export interface ProjectData {
  graph: GraphData;
  reference: Record<string, unknown>;
  created_at: {
    seconds: number;
  };
}
