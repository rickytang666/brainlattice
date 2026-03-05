"""
Test local PDF ingestion pipeline end-to-end.
Produces output_graph.json with the knowledge graph.

Usage:
  1. Start backend: cd backend && uvicorn main:app --reload
  2. Run: python scripts/test_local_pipeline.py --file path/to/doc.pdf
  3. Graph saved to output_graph.json (or --output other.json)
"""
import requests
import time
import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# load .env from backend/ when run from project root or backend/
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

BASE_URL = "http://localhost:8000/api"

def run_test(
    pdf_path: str,
    gemini_key: str = None,
    openai_key: str = None,
    openrouter_key: str = None,
    output_file: str = None,
):
    path = Path(pdf_path)
    if not path.exists():
        print(f"error: could not find {pdf_path}")
        sys.exit(1)

    if not gemini_key:
        print("error: GEMINI_API_KEY required. set in .env or pass --gemini-key")
        sys.exit(1)
    if not openrouter_key:
        print("error: OPENROUTER_API_KEY required. set in .env or pass --openrouter-key")
        sys.exit(1)

    print(f"uploading {path.name} to local backend...")
    
    headers = {
        "X-User-Id": "local-test-user"
    }
    if gemini_key:
        headers["X-Gemini-API-Key"] = gemini_key
    if openai_key:
        headers["X-OpenAI-API-Key"] = openai_key
    if openrouter_key:
        headers["X-OpenRouter-API-Key"] = openrouter_key
        
    with open(path, "rb") as f:
        files = {"file": (path.name, f, "application/pdf")}
        try:
            res = requests.post(f"{BASE_URL}/ingest/upload", files=files, headers=headers)
            if res.status_code == 422:
                print(f"validation error: {res.text}")
            res.raise_for_status()
        except requests.exceptions.ConnectionError:
            print("error: is the backend running? run `uvicorn main:app` in another terminal.")
            sys.exit(1)

    data = res.json()
    job_id = data.get("job_id")
    
    if not job_id:
        print("failed to get job_id from upload:", data)
        sys.exit(1)
        
    print(f"success! job created: {job_id}")
    print("polling status...")
    
    # poll the status endpoint
    while True:
        try:
            status_res = requests.get(f"{BASE_URL}/ingest/status/{job_id}")
            status_res.raise_for_status()
            status_data = status_res.json()
            
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            
            # neat little progress bar
            bar_length = 30
            filled = int(bar_length * (float(progress) / 100))
            bar = '█' * filled + '-' * (bar_length - filled)
            
            sys.stdout.write(f"\r[{bar}] {progress}% | status: {status}")
            sys.stdout.flush()
            
            if status == "completed":
                print("\n\n✅ ingestion pipeline complete!")
                result = status_data.get("result", {})
                metadata = status_data.get("metadata", {})
                
                if isinstance(result, str):
                    result = json.loads(result)
                    
                timings = result.get("timings", {})
                if timings:
                    print("\n⏱️  --- pipeline timings ---")
                    for k, v in timings.items():
                        print(f"  - {k.replace('_', ' ').title()}: {v:.2f}s")
                
                if "timings" in result:
                    del result["timings"]
                    
                print("\n--- results summary ---")
                print(json.dumps(result, indent=2))
                
                # fetch and save graph json
                project_id = metadata.get("project_id")
                if project_id and output_file:
                    print(f"\nfetching graph json for project {project_id}...")
                    graph_res = requests.get(
                        f"{BASE_URL}/project/{project_id}/graph",
                        headers=headers
                    )
                    graph_res.raise_for_status()
                    graph_data = graph_res.json()
                    
                    with open(output_file, "w") as out:
                        json.dump(graph_data, out, indent=2)
                    print(f"saved full graph json to {output_file}!")
                elif output_file:
                    print(f"\ncould not find project_id, saving graph preview instead...")
                    with open(output_file, "w") as out:
                        json.dump(result.get("graph_preview", {}), out, indent=2)
                    print(f"saved graph preview to {output_file}!")
                    
                break
            elif status == "failed":
                print("\n\n❌ ingestion failed!")
                result = status_data.get("result", {})
                if isinstance(result, str):
                    result = json.loads(result)
                print(f"error details: {result.get('error')}")
                break
                
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            print(f"\nerror checking status: {e}")
            sys.exit(1)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test local PDF ingestion pipeline.")
    parser.add_argument("--file", required=True, help="Path to PDF file to test.")
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    parser.add_argument("--openai-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--openrouter-key", default=os.getenv("OPENROUTER_API_KEY"), help="OpenRouter API key (required)")
    parser.add_argument("--output", default="output_graph.json", help="Save graph JSON to file (default: output_graph.json)")
    args = parser.parse_args()

    run_test(args.file, args.gemini_key, args.openai_key, args.openrouter_key, args.output)
