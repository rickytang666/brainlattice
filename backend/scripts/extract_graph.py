import os
import sys
import asyncio
import json
from pathlib import Path

# add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm.graph_extractor import GraphExtractor
from services.graph.builder import GraphBuilder

async def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/extract_graph.py <filename_in_data_folder>")
        sys.exit(1)

    filename = sys.argv[1]
    data_dir = Path("data")
    md_path = data_dir / filename
    
    if not md_path.exists():
        print(f"error: {md_path} not found.")
        sys.exit(1)

    print(f"reading {md_path}...")
    with open(md_path, "r") as f:
        content = f.read()

    extractor = GraphExtractor()
    builder = GraphBuilder()
    
    # 50k chars per window, overlap 5k
    window_size = 50000
    overlap = 5000
    text_len = len(content)
    windows = []
    
    if text_len <= window_size:
        windows.append(content)
    else:
        start = 0
        while start < text_len:
            end = min(start + window_size, text_len)
            windows.append(content[start:end])
            if end == text_len:
                break
            start += (window_size - overlap)

    print(f"processing {len(windows)} windows...")
    accumulated_nodes = []
    extracted_graphs = []
    
    # 1. Pass 1: Extract Core Concepts from Skeleton (H1/H2)
    import re
    headers = []
    for line in content.split('\n'):
        if re.match(r'^#{1,2}\s+', line):
            headers.append(line.strip())
    skeleton = "\n".join(headers)
    print(f"extracted skeleton context: {len(skeleton)} chars")

    if skeleton:
        print("identifying core concepts from skeleton...")
        skeleton_graph = await extractor.extract_from_skeleton(skeleton)
        accumulated_nodes.extend(skeleton_graph.nodes)
        extracted_graphs.append(skeleton_graph)
        print(f"seeded {len(skeleton_graph.nodes)} core concepts.")

    # 2. Pass 2: Extract from Text Windows
    for i, window_text in enumerate(windows):
        print(f"extracting window {i+1}/{len(windows)}...")
        concept_ids = [n.id for n in accumulated_nodes]
        graph_data = await extractor.extract_from_window(window_text, existing_concepts=concept_ids)
        extracted_graphs.append(graph_data)
        accumulated_nodes.extend(graph_data.nodes)
        
    print("resolving and merging graph...")
    final_graph = builder.build(extracted_graphs)
    
    # 3. Connectivity: Connect Orphans
    from services.graph.connector import GraphConnector
    connector = GraphConnector()
    print("connecting orphan components...")
    connected_graph = connector.connect_orphans(final_graph)
    
    output_path = md_path.with_suffix(".json")
    with open(output_path, "w") as f:
        json.dump(connected_graph.model_dump(), f, indent=2)
    
    print(f"saved graph to {output_path}")
    print(f"total nodes: {len(connected_graph.nodes)}")

if __name__ == "__main__":
    asyncio.run(main())
