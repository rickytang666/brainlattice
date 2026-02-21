from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Header
from core.dependencies import get_user_context, UserContext
from services.storage_service import S3StorageService
from services.job_service import get_job_service

from core.config import get_settings
import uuid
import os

router = APIRouter()
settings = get_settings()

@router.post("/ingest/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context: UserContext = Depends(get_user_context)
):
    """
    uploads file to r2, creates job in redis, triggers async worker via qstash or locally
    """
    try:
        from services.ingestion_orchestrator import IngestionOrchestrator
        orchestrator = IngestionOrchestrator()
        
        content = await file.read()
        result = await orchestrator.init_ingestion(
            file.filename, 
            content, 
            background_tasks=background_tasks,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ingest failed: {str(e)}")

@router.get("/ingest/status/{job_id}")
async def get_status(job_id: str):
    """check job status"""
    jobs = get_job_service()
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

@router.post("/ingest/retry/{job_id}")
async def retry_ingest(
    job_id: str, 
    background_tasks: BackgroundTasks,
    context: UserContext = Depends(get_user_context)
):
    """manually retry a failed ingestion job using its ID"""
    try:
        from services.ingestion_orchestrator import IngestionOrchestrator
        orchestrator = IngestionOrchestrator()
        result = await orchestrator.retry_ingestion(
            job_id, 
            background_tasks=background_tasks,
            user_id=context.user_id,
            gemini_key=context.gemini_key,
            openai_key=context.openai_key
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"retry failed: {str(e)}")
