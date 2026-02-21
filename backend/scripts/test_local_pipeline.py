import requests
import time
import sys
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api"

def run_test(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f"error: could not find {pdf_path}")
        sys.exit(1)

    print(f"uploading {path.name} to local backend...")
    
    with open(path, "rb") as f:
        files = {"file": (path.name, f, "application/pdf")}
        try:
            res = requests.post(f"{BASE_URL}/ingest/upload", files=files)
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
                if isinstance(result, str):
                    result = json.loads(result)
                print("\n--- results summary ---")
                print(json.dumps(result, indent=2))
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
    args = parser.parse_args()
    
    run_test(args.file)
