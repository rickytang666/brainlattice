import type { GraphData } from "../types/graph";
import calculus from "./json/calculus.json";
import linearAlgebra from "./json/linear-algebra.json";

export const EXAMPLES: Record<string, GraphData> = {
  calculus: ((calculus as any).graph_preview || calculus) as unknown as GraphData,
  linearAlgebra: ((linearAlgebra as any).graph_preview || linearAlgebra) as unknown as GraphData
};
