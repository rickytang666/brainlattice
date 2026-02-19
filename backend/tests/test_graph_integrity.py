import json
import os
import pytest
from pathlib import Path

def get_graph_files():
    """finds all .json files in /data"""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return list(data_dir.glob("*.json"))

@pytest.mark.parametrize("graph_path", get_graph_files())
def test_graph_integrity(graph_path):
    """
    validates that the graph is a clean adjacency list:
    1. all outbound_links must point to a node that exists in the graph.
    2. no self-loops (optional, but good for clean graphs).
    3. proper id formatting (lowercase, spaces).
    """
    with open(graph_path, "r") as f:
        data = json.load(f)
    
    nodes = data.get("nodes", [])
    assert len(nodes) > 0, f"graph {graph_path} is empty"
    
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

    # final report
    if errors:
        pytest.fail(f"graph integrity failed for {graph_path.name}:\n" + "\n".join(errors))
    else:
        print(f"{graph_path.name} is a valid conceptual network.")
