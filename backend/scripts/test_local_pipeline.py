import requests
import time
import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000/api"

def run_test(pdf_path: str, gemini_key: str = None, openai_key: str = None, output_file: str = None):
    path = Path(pdf_path)
    if not path.exists():
        print(f"error: could not find {pdf_path}")
        sys.exit(1)

    print(f"uploading {path.name} to local backend...")
    
    headers = {
        "X-User-Id": "local-test-user"
    }
    if gemini_key:
        headers["X-Gemini-API-Key"] = gemini_key
    if openai_key:
        headers["X-OpenAI-API-Key"] = openai_key
        
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
                print("\n--- results summary ---")
                print(json.dumps(result, indent=2))
                
                # if user wants to save the json, fetch and save it
                project_id = metadata.get("project_id")
                if output_file and project_id:
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
    parser.add_argument("--file", default="data/math119.pdf", help="Path to PDF file to test.")
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API key")
    parser.add_argument("--openai-key", default=os.getenv("OPENAI_API_KEY"), help="OpenAI API key")
    parser.add_argument("--output", default=None, help="Save the resulting JSON graph to a file (e.g., my_graph.json)")
    args = parser.parse_args()
    
    run_test(args.file, args.gemini_key, args.openai_key, args.output)
