import json
import os
import pytest
import networkx as nx
from pathlib import Path

# minimal valid graph for when data/ has no files (ensures test logic always runs)
FALLBACK_GRAPH = {
    "nodes": [
        {"id": "calculus", "outbound_links": ["limit", "derivative"]},
        {"id": "limit", "outbound_links": ["calculus"]},
        {"id": "derivative", "outbound_links": []},
    ]
}


def get_graph_files():
    """finds all .json files in data/; returns [(path, data)] for parametrize."""
    data_dir = Path("data")
    if not data_dir.exists():
        return [("fallback", FALLBACK_GRAPH)]
    files = list(data_dir.glob("*.json"))
    if not files:
        return [("fallback", FALLBACK_GRAPH)]
    result = []
    for p in files:
        with open(p, "r") as f:
            result.append((str(p), json.load(f)))
    return result


def _get_graph_id(item):
    return item[0] if isinstance(item, tuple) else str(item)


@pytest.mark.parametrize("graph_path,graph_data", get_graph_files(), ids=_get_graph_id)
def test_graph_integrity(graph_path, graph_data):
    """
    Validates graph integrity: adjacency list validity, no self-loops,
    proper id formatting (lowercase, spaces), and connectivity.
    Uses data/*.json when present; otherwise runs with a minimal fallback graph.
    """
    nodes = graph_data.get("nodes", [])
    assert len(nodes) > 0, f"graph {graph_path!r} is empty"
    
    # map for O(1) existence checks
    node_ids = {n["id"] for n in nodes}
    
    errors = []
    for node in nodes:
        node_id = node["id"]
        
        # 1. check id formatting
        if node_id != node_id.lower() or "_" in node_id:
            errors.append(f"Format error: Node ID '{node_id}' should be lowercase with spaces.")
            
        # 2. check directed links (adjacency list validity)
        outbound = node.get("outbound_links", [])
        for link in outbound:
            if link not in node_ids:
                errors.append(f"Dangling link: {node_id} -> {link} (Node '{link}' does not exist)")
            
            if link == node_id:
                errors.append(f"Self-loop: {node_id} points to itself")

    # 3. check connectivity (orphans)
    if node_ids:
        G = nx.Graph()
        G.add_nodes_from(node_ids)
        for node in nodes:
            for target in node.get("outbound_links", []):
                if target in node_ids:
                    G.add_edge(node["id"], target)
        
        components = list(nx.connected_components(G))
        if len(components) > 1:
            errors.append(f"graph is fragmented into {len(components)} disconnected parts.")
            components.sort(key=len, reverse=True)
            for i, comp in enumerate(components[1:], start=2):
                if len(comp) < 5:
                    errors.append(f"  part {i}: {list(comp)}")
                else:
                    errors.append(f"  part {i}: {len(comp)} nodes")

    # final report
    name = Path(graph_path).name if graph_path != "fallback" else graph_path
    if errors:
        pytest.fail(f"graph integrity failed for {name}:\n" + "\n".join(errors))
    else:
        print(f"{name} is a valid conceptual network.")
