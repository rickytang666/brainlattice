from mangum import Mangum
from main import app
import json

# 1. api handler
api_handler = Mangum(app)

# 2. worker handler
def worker_handler(event, context):
    """
    processor for async background tasks
    trigger: qstash webhook -> lambda url
    payload: {"job_id": "...", "file_key": "..."}
    """
    print(f"worker received event: {json.dumps(event)}")
    
    # parsing body from qstash (usually comes as json body string)
    try:
        body = event.get("body")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body or {}
            
        job_id = payload.get("job_id")
        file_key = payload.get("file_key")
        
        if not job_id or not file_key:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "missing job_id or file_key"})
            }
            
        print(f"processing job: {job_id} for file: {file_key}")
        
        # TODO: call actual processing logic here
        # process_file_task(job_id, file_key)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "processing_started", "job_id": job_id})
        }
        
    except Exception as e:
        print(f"worker error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
