from typing import Dict
import networkx as nx
from schemas.graph import GraphData

class GraphMetrics:
    """
    Computes graph theory metrics (PageRank, centrality, etc.) for the conceptual network.
    """

    @staticmethod
    def calculate_pagerank(graph: GraphData) -> Dict[str, float]:
        """Calculates PageRank for all nodes based on directed outbound edges."""
        G = nx.DiGraph()
        
        for node in graph.nodes:
            G.add_node(node.id)
            for neighbor in node.outbound_links:
                G.add_edge(node.id, neighbor)
                
        if len(G) == 0:
            return {}
            
        return nx.pagerank(G)
