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
        action = payload.get("action", "ingest") # default to ingest for backward compatibility
        
        gemini_key = payload.get("gemini_key")
        openai_key = payload.get("openai_key")
        user_id = payload.get("user_id")
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if action == "ingest":
            if not job_id or not file_key:
                return {"statusCode": 400, "body": "missing job_id or file_key"}
                
            from services.ingestion_processor import IngestionProcessor
            processor = IngestionProcessor(
                job_id=job_id, 
                file_key=file_key,
                gemini_key=gemini_key,
                openai_key=openai_key,
                user_id=user_id
            )
            
            result = loop.run_until_complete(processor.process())
            
        elif action == "prepare_export":
            project_id = payload.get("project_id")
            if not project_id:
                return {"statusCode": 400, "body": "missing project_id for export"}
                
            from services.export_processor import ExportProcessor
            processor = ExportProcessor(
                project_id=project_id,
                user_id=user_id,
                gemini_key=gemini_key,
                openai_key=openai_key
            )
            
            result = loop.run_until_complete(processor.process())
            
        else:
            return {"statusCode": 400, "body": f"unknown action: {action}"}
            
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
