from typing import List, Set, Dict, Any
import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from schemas.graph import GraphData, GraphNode
from services.embedding_service import EmbeddingService
import logging

logger = logging.getLogger(__name__)

class GraphConnector:
    """
    connects orphan components to the main graph using semantic similarity.
    acts as a fallback to ensure 100% connectivity.
    """

    def __init__(self):
        self.embeddings = EmbeddingService()

    def connect_orphans(self, graph_data: GraphData) -> GraphData:
        # 1. build networkx graph (undirected for component analysis)
        G = nx.Graph()
        node_map = {n.id: n for n in graph_data.nodes}
        G.add_nodes_from(node_map.keys())
        
        for n in graph_data.nodes:
            for target in n.outbound_links:
                if target in node_map:
                    G.add_edge(n.id, target)
        
        # 2. identify components
        components = list(nx.connected_components(G))
        if len(components) <= 1:
            logger.info("graph is already fully connected.")
            return graph_data
            
        # sort by size (largest is main)
        components.sort(key=len, reverse=True)
        main_component = components[0]
        orphans = components[1:]
        
        logger.info(f"dimensions: main component={len(main_component)} nodes. orphans={len(orphans)}.")
        
        # 3. get embeddings for main component representatives
        # we take top nodes by degree to represent the "core" of the main cluster
        main_reps = self._get_representatives(G, main_component, limit=50)
        if not main_reps:
            return graph_data
            
        try:
            main_emb = self.embeddings.get_embeddings(main_reps)
        except Exception as e:
            logger.error(f"failed to get embeddings for main component: {e}")
            return graph_data

        # 4. link each orphan
        for orphan in orphans:
            orphan_reps = self._get_representatives(G, orphan, limit=10)
            if not orphan_reps:
                continue
                
            try:
                orphan_emb = self.embeddings.get_embeddings(orphan_reps)
                
                # compute similarity matrix (orphans x main)
                # shape: [len(orphan_reps), len(main_reps)]
                sim_matrix = cosine_similarity(orphan_emb, main_emb)
                
                # find best pair
                i, j = np.unravel_index(sim_matrix.argmax(), sim_matrix.shape)
                best_orphan_node = orphan_reps[i]
                best_main_node = main_reps[j]
                score = sim_matrix[i, j]
                
                if score > 0.25: # lenient threshold to ensure connectivity
                    logger.info(f"bridging orphan '{best_orphan_node}' -> main '{best_main_node}' (score: {score:.2f})")
                    
                    # update graph data objects
                    orphan_obj = node_map[best_orphan_node]
                    main_obj = node_map[best_main_node]
                    
                    # add bidirectional link (parent/child is ambiguous, so we do both or inferred)
                    if best_main_node not in orphan_obj.outbound_links:
                        orphan_obj.outbound_links.append(best_main_node)
                    
                    # also update inbound for consistency
                    if best_orphan_node not in main_obj.inbound_links:
                        main_obj.inbound_links.append(best_orphan_node)
                else:
                    logger.warning(f"Orphan {orphan_reps[0]}... has no close semantic match (max: {score:.2f})")
                    
            except Exception as e:
                logger.error(f"Failed to bridge orphan component {orphan_reps}: {e}")
                continue

        return graph_data

    def _get_representatives(self, G: nx.Graph, component: Set[str], limit: int = 5) -> List[str]:
        """selects high-degree nodes to represent a cluster"""
        subgraph = G.subgraph(component)
        # sort by degree (descending)
        nodes_by_degree = sorted(subgraph.degree, key=lambda x: x[1], reverse=True)
        # return IDs
        return [n for n, d in nodes_by_degree[:limit]]
