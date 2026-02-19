import asyncio
import json
import os
import sys

# add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# load env vars from .env
load_dotenv()

from services.llm.graph_extractor import GraphExtractor
from services.graph_service import GraphService
from schemas.graph import GraphData

async def test_graph_local():
    print("--- Starting Local Directed Graph Test (Space-Separated IDs) ---")
    
    sample_text = """
    Artificial Intelligence (AI) is a branch of computer science.
    Neural Networks are a key part of AI.
    Deep Learning focuses on deep neural networks.
    Backpropagation is used to train neural nets.
    Transformers have revolutionized AI with its attention mechanism.
    Large Language Models (LLMs) like GPT are based on transformers.
    """
    
    extractor = GraphExtractor()
    print("Extracting concepts using Gemini...")
    graph_data_1 = await extractor.extract_from_window(sample_text)
    
    service = GraphService()
    print("Resolving entities and building directed graph...")
    final_graph = service.build_graph([graph_data_1])
    
    print("\n--- Final Resolved Directed Graph ---")
    
    for node in final_graph.nodes:
        print(f"\n[NODE] {node.id}")
        if node.aliases:
            print(f"  Aliases : {', '.join(node.aliases)}")
        if node.outbound_links:
            print(f"  Outbound: {', '.join(node.outbound_links)}")
        if node.inbound_links:
            print(f"  Inbound : {', '.join(node.inbound_links)}")
            
    print("\n--- End of Test ---")

if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("ERROR: GEMINI_API_KEY and OPENAI_API_KEY must be set in .env")
    else:
        asyncio.run(test_graph_local())
