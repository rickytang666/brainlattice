from mangum import Mangum
from main import app
import json
import os
import asyncio

# pipeline services
from db.session import get_db, SessionLocal
from db import models

# api handler
api_handler = Mangum(app)

# worker handler
def worker_handler(event, context):
    """
    processes async background tasks triggered by qstash webhook
    """
    print(f"[WORKER] received event: {json.dumps(event)}")
    
    try:
        # extract payload
        body = event.get("body")
        payload = json.loads(body) if isinstance(body, str) else (body or {})
            
        job_id = payload.get("job_id")
        file_key = payload.get("file_key")
        
        if not job_id or not file_key:
            return {"statusCode": 400, "body": "missing job_id or file_key"}
            
        # delegate to pipeline service
        from services.ingestion_processor import IngestionProcessor
        processor = IngestionProcessor(job_id, file_key)
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        result = loop.run_until_complete(processor.process())
            
        return {
            "statusCode": 200, 
            "body": json.dumps({"status": "completed", **result})
        }

    except Exception as e:
        print(f"[WORKER] fatal error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
