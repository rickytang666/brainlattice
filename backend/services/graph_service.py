from typing import List, Dict, Set
from schemas.graph import GraphData, GraphNode
from services.embedding_service import EmbeddingService
from sklearn.cluster import AgglomerativeClustering
from collections import Counter
import numpy as np
import networkx as nx

class GraphService:
    """
    manages graph construction, deduplication, and analysis.
    """
    
    def __init__(self):
        self.embedder = EmbeddingService()
        self.clustering_threshold = 0.85 # similarity threshold (0.85 cosine sim)
        
    def resolve_entities(self, raw_nodes: List[GraphNode]) -> Dict[str, str]:
        """
        uses embedding clustering to find near-duplicate entities.
        returns a map of {original_id: canonical_id}.
        """
        if not raw_nodes:
            return {}
            
        node_ids = list(set([n.id for n in raw_nodes]))
        if len(node_ids) < 2:
            return {n: n for n in node_ids}
            
        embeddings = self.embedder.get_embeddings(node_ids)
        X = np.array(embeddings)
        
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0] = 1
        X_norm = X / norms
        
        dist_threshold = np.sqrt(2 * (1 - self.clustering_threshold))
        
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=dist_threshold,
            metric="euclidean",
            linkage="average"
        )
        labels = clustering.fit_predict(X_norm)
        
        clusters = {}
        for node_id, label in zip(node_ids, labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(node_id)
            
        id_map = {}
        original_counts = Counter([n.id for n in raw_nodes])
        
        for label, group in clusters.items():
            canonical = max(group, key=lambda x: original_counts[x])
            for node_id in group:
                id_map[node_id] = canonical
                
        return id_map

    def build_graph(self, windows_data: List[GraphData]) -> GraphData:
        """
        merges multiple window graphs and computes inbound backlinks.
        """
        all_nodes = []
        for w in windows_data:
            all_nodes.extend(w.nodes)
            
        print(f"[GRAPH] resolving {len(all_nodes)} raw occurrences...")
        id_map = self.resolve_entities(all_nodes)
        
        final_nodes: Dict[str, GraphNode] = {}
        
        # 1. merge nodes and outbound links
        for n in all_nodes:
            canonical = id_map.get(n.id, n.id)
            
            if canonical not in final_nodes:
                final_nodes[canonical] = GraphNode(
                    id=canonical, 
                    aliases=n.aliases,
                    outbound_links=[],
                    inbound_links=[]
                )
            
            target_node = final_nodes[canonical]
            
            # merge aliases
            new_aliases = set(target_node.aliases)
            new_aliases.update(n.aliases)
            if n.id != canonical:
                new_aliases.add(n.id)
            target_node.aliases = list(new_aliases)
            
            # merge outbound links (remapped)
            for link in n.outbound_links:
                 remapped_link = id_map.get(link, link)
                 if remapped_link != canonical and remapped_link not in target_node.outbound_links:
                     target_node.outbound_links.append(remapped_link)
        
        # 2. compute inbound links
        print("[GRAPH] computing inbound backlinks...")
        for node_id, node in final_nodes.items():
            for target_id in node.outbound_links:
                if target_id in final_nodes:
                    if node_id not in final_nodes[target_id].inbound_links:
                        final_nodes[target_id].inbound_links.append(node_id)
                     
        return GraphData(nodes=list(final_nodes.values()))

    def calculate_metrics(self, graph_data: GraphData):
        """
        calculates pagerank from outbound_links
        """
        G = nx.DiGraph()
        for node in graph_data.nodes:
            G.add_node(node.id)
            for link in node.outbound_links:
                G.add_edge(node.id, link)
            
        return nx.pagerank(G)
