from typing import List, Dict, Set
from schemas.graph import GraphData, GraphNode
from services.graph.resolver import EntityResolver

class GraphBuilder:
    """
    merges raw graph occurrences into consolidated conceptual network
    computes bidirectional dependencies (inbound/outbound links)
    """

    def __init__(self, resolver: EntityResolver = None):
        self.resolver = resolver or EntityResolver()

    def build(self, extracted_graphs: List[GraphData]) -> GraphData:
        """merges multiple extracted graphs into one deduplicated result"""
        raw_nodes = []
        for g in extracted_graphs:
            raw_nodes.extend(g.nodes)

        # resolve entity mapping (original_id -> canonical_id)
        id_map = self.resolver.get_id_map(raw_nodes)
        
        # consolidate nodes
        final_nodes: Dict[str, GraphNode] = {}
        
        for n in raw_nodes:
            canonical = id_map.get(n.id, n.id)
            
            if canonical not in final_nodes:
                final_nodes[canonical] = GraphNode(
                    id=canonical,
                    aliases=[],
                    outbound_links=[],
                    inbound_links=[]
                )
            
            target = final_nodes[canonical]
            
            # merge aliases
            all_aliases = set(target.aliases)
            all_aliases.update(n.aliases)
            if n.id != canonical:
                all_aliases.add(n.id)
            target.aliases = list(all_aliases)
            
            # merge outbound links (remap targets)
            for raw_link in n.outbound_links:
                remapped_link = id_map.get(raw_link, raw_link)
                if remapped_link != canonical and remapped_link not in target.outbound_links:
                    target.outbound_links.append(remapped_link)
        
        # compute inbound links
        for node_id, node in final_nodes.items():
            for target_id in node.outbound_links:
                if target_id in final_nodes:
                    if node_id not in final_nodes[target_id].inbound_links:
                        final_nodes[target_id].inbound_links.append(node_id)
                        
        return GraphData(nodes=list(final_nodes.values()))
